#include "settings.h"

#include <ESP8266WiFi.h>
#include <WiFiUDP.h>
#include <WiFiClient.h>
#include <Adafruit_NeoPixel.h>

const byte MAC_LENGTH = 6;
const byte BYTESPERPIXEL = 4;

WiFiUDP GHeartbeatSocket;
WiFiServer GRequestServer( SERVER_PORT );
Adafruit_NeoPixel GPixels( NUM_PIXELS, PIN_PIXELS, NEO_GRB + NEO_KHZ800 );

enum class ERequestStatus : unsigned int {
  RS_Success = 0,
  RS_OtherError,
  RS_ToLargePayload,
  RS_ToSmallPayload,
  RS_BadMac
};

// Simple software timer class.
class Timer
{
public:
  void (*Callback_Start)();
  void (*Callback_Tick)();
  void (*Callback_Stop)();

public:
  Timer() :
    Callback_Start( nullptr ),
    Callback_Tick( nullptr ),
    Callback_Stop( nullptr ),
    mStartTime( 0 ),
    mInterval( -1 ),
    mLooping( false )
  {}

  /** @param interval Time in ms. */
  void Start( int interval, bool looping )
  {
    if( interval >= 0 )
    {
      mInterval = interval;
      mLooping = looping;
      mStartTime = millis();
    
      if( Callback_Start ) Callback_Start();
    }
  }
  
  void Update()
  {
    if( IsActive() )
    {
      unsigned long now = millis();
      if( now - mStartTime > mInterval )
      {
        if( Callback_Tick ) Callback_Tick();
        
        if( !mLooping )
          Stop();
        else
          mStartTime = now;
      }
    }
  }

  void Stop()
  {
    if( IsActive() )
    {
      mInterval = -1;

      if( Callback_Stop ) Callback_Stop();
    }
  }

  inline bool IsActive() const
  {
    return mInterval >= 0;
  }
  
private:
  unsigned long mStartTime;
  int mInterval;
  bool mLooping;
};

void SendHeartbeat()
{
  char message[ 128 ];
  byte mac[ 6 ];
  WiFi.macAddress( mac );

  message[0] = 'D';
  message[1] = 'L';
  message[2] = mac[0];
  message[3] = mac[1];
  message[4] = mac[2];
  message[5] = mac[3];
  message[6] = mac[4];
  message[7] = mac[5];
  message[8] = SERVER_PORT >> 8;
  message[9] = SERVER_PORT;

  const int len = 10;

  GHeartbeatSocket.beginPacket( CHECKIN_IP, CHECKIN_PORT );
  GHeartbeatSocket.write( message, len );
  GHeartbeatSocket.endPacket();
}

Timer GHeartbeatTimer;

void setup() {
  WiFi.begin( WIFI_SSID, WIFI_PASSWORD );
  while( WiFi.status() != WL_CONNECTED ) {
    delay( 10 );
  }

  GRequestServer.begin();

  SendHeartbeat();
  GHeartbeatTimer.Callback_Tick = &SendHeartbeat;
  GHeartbeatTimer.Start( HEARTBEAT_INTERVAL, true );
  GPixels.begin();
  GPixels.show();
}


ERequestStatus GHandleConnection( WiFiClient connection )
{
  if( connection.connected() )
  {
    while( connection.available() < MAC_LENGTH )
    {
      delay( 1 );
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
     || device_mac[ 5 ] != mac[ 5 ]
     || device_mac[ 6 ] != mac[ 6 ] )
     {
      return ERequestStatus::RS_BadMac;
     }
    while( connection.available() )
    {
      while( connection.available() < BYTESPERPIXEL )
      {
        delay( 1 );
      }
      byte pixelPayload[ BYTESPERPIXEL ];
      uint8_t pixelPayloadLenght = connection.read( pixelPayload, BYTESPERPIXEL );
      
      GPixels.setPixelColor( pixelPayload[0], pixelPayload[1], pixelPayload[2], pixelPayload[3] );    
    }
    GPixels.show();
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

