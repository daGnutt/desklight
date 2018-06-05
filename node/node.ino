#include "timer.h"
#include "settings.h"

#include <ESP8266WiFi.h>
#include <WiFiUDP.h>
#include <WiFiClient.h>
#include <Adafruit_NeoPixel.h>

#if BOARD_DEVELOPMENT
#define DEV_SERIAL_PRINT( x ) Serial.print( x )
#define DEV_SERIAL_PRINTLN( x ) Serial.println( x )
#define DEV_SERIAL_PRINTF( x, ... ) Serial.printf( x, __VA_ARGS__ );
#else
#define DEV_SERIAL_PRINT( x )
#define DEV_SERIAL_PRINTLN( x )
#define DEV_SERIAL_PRINTF( x, ... )
#endif


const byte MAC_LENGTH = 6;
const byte BYTESPERPIXEL = 4;

WiFiUDP GHeartbeatSocket;
WiFiServer GRequestServer( SERVER_PORT );
Adafruit_NeoPixel GPixels( NUM_PIXELS, PIN_PIXELS, NEO_GRB + NEO_KHZ800 );

enum class ERequestStatus : unsigned int {
  RS_Success = 0,
  RS_BadMac,
  RS_BadPayload,
  RS_Timeout
};

Timer GHeartbeatTimer;
uint8_t scenecounter;

void SendHeartbeat()
{
  char message[ 128 ];
  byte mac[ 6 ];
  WiFi.macAddress( mac );

  message[0]  = 'D';
  message[1]  = 'L';
  message[2]  = mac[0];
  message[3]  = mac[1];
  message[4]  = mac[2];
  message[5]  = mac[3];
  message[6]  = mac[4];
  message[7]  = mac[5];
  message[8]  = SERVER_PORT >> 8;
  message[9]  = SERVER_PORT;
  message[10] = scenecounter;

  const int len = 11;

  GHeartbeatSocket.beginPacket( CHECKIN_IP, CHECKIN_PORT );
  GHeartbeatSocket.write( message, len );
  GHeartbeatSocket.endPacket();
}

void setup() {
#if BOARD_DEVELOPMENT
  Serial.begin( 115200 );
  delay( 10 );
#endif

  DEV_SERIAL_PRINTLN( "Connecting to " );
  DEV_SERIAL_PRINTLN( WIFI_SSID );
  WiFi.begin( WIFI_SSID, WIFI_PASSWORD );
  while( WiFi.status() != WL_CONNECTED ) {
    delay( 100 );
    DEV_SERIAL_PRINT( "." );
  }
  DEV_SERIAL_PRINTLN( "" );
  DEV_SERIAL_PRINTLN( "WiFi connected" );
  DEV_SERIAL_PRINTLN( " IP: " );
  DEV_SERIAL_PRINTLN( WiFi.localIP() );

  byte mac[ 6 ];
  WiFi.macAddress( mac );
  DEV_SERIAL_PRINTF( " MAC: %02x:%02x:%02x:%02x:%02x:%02x\n", mac[ 0 ], mac[ 1 ], mac[ 2 ], mac[ 3 ], mac[ 4 ], mac[ 5 ] );


  GRequestServer.begin();

  SendHeartbeat();
  GHeartbeatTimer.Callback_Tick = &SendHeartbeat;
  GHeartbeatTimer.Start( HEARTBEAT_INTERVAL, true );
  GPixels.begin();
  GPixels.show();

  scenecounter = 0;
}


ERequestStatus GHandleConnection( WiFiClient connection )
{
  DEV_SERIAL_PRINTLN( "Handling incoming connection" );
  if( connection.connected() )
  {
    unsigned long startOfConnection = millis();
    unsigned long currentTime;
    while( connection.available() < MAC_LENGTH )
    {
      if( connection.status() == 0 )
      {
        return ERequestStatus::RS_BadMac;
      }
      delay( 1 );
      currentTime = millis();
      if( currentTime - startOfConnection > 1000 )
      {
        return ERequestStatus::RS_Timeout;
      }
    }

    byte device_mac[ 6 ];
    WiFi.macAddress( device_mac );
    
    byte mac[ MAC_LENGTH ];
    uint8_t mac_length = connection.read( mac, MAC_LENGTH );

    if( device_mac[ 0 ] != mac[ 0 ]
     || device_mac[ 1 ] != mac[ 1 ]
     || device_mac[ 2 ] != mac[ 2 ]
     || device_mac[ 3 ] != mac[ 3 ]
     || device_mac[ 4 ] != mac[ 4 ]
     || device_mac[ 5 ] != mac[ 5 ] )
     {
      return ERequestStatus::RS_BadMac;
     }
    while( connection.available() )
    {
      while( connection.available() < BYTESPERPIXEL )
      {
        if( connection.status() == 0 )
        {
          return ERequestStatus::RS_BadPayload;
        }
                
        delay( 1 );
        if( millis() - startOfConnection > 1000 )
        {
         return ERequestStatus::RS_Timeout;
        }
      }
      byte pixelPayload[ BYTESPERPIXEL ];
      uint8_t pixelPayloadLenght = connection.read( pixelPayload, BYTESPERPIXEL );
      
      GPixels.setPixelColor( pixelPayload[0], pixelPayload[1], pixelPayload[2], pixelPayload[3] );    
    }
    GPixels.show();
    scenecounter++;
  }
  return ERequestStatus::RS_Success;
}

void loop() {
  GHeartbeatTimer.Update();
  WiFiClient connection = GRequestServer.available();
  if( connection ) {
    ERequestStatus result = GHandleConnection( connection );
    connection.write( (uint8_t)result );
    connection.stop();
  }
}
