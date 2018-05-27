#!/usr/bin/env python3

"""webhandler.py: """

__author__ = "Gnutt Halvordsson"

import binascii
import json
import os
import socket
import struct
import threading
import urllib

getBeacons = None
beaconbasescene = {}

def do_GET(request):
  parsedurl = urllib.parse.urlparse( request.path )

  if parsedurl.path == '/nodes':
    GETBeacons(request)
    return

  if parsedurl.path == '/scenes':
    GETScenes(request)
    return

  servefile(request)

def do_POST(request):
  if request.path == '/setscene':
    POSTsetscene(request)
    return

  request.send_response_only(500)
  request.end_headers()
  request.wfile.write('NOT IMPLEMTEND'.encode())

def GETBeacons(request):
  request.send_response_only(200)
  request.end_headers()
  data = json.dumps( getBeacons() )
  request.wfile.write( data.encode() )
  return

def GETScenes(request):
  parsedurl = urllib.parse.urlparse( request.path )
  querystring = urllib.parse.parse_qs( parsedurl.query )

  if 'node' not in querystring:
    request.send_response_only(501)
    request.end_headers()
    request.wfile.write("Missing node".encode())
    return

  with open("scenes.json", mode="r") as fp:
    scenes = fp.read()

  scenes = json.loads( scenes )
  if querystring['node'][0] not in scenes:
    request.send_response_only(500)
    request.end_headers()
    request.wfile.write( 'Node not found'.encode() )
    return

  request.send_response_only(200)
  request.end_headers()
  request.wfile.write( json.dumps( scenes[querystring['node'][0]] ).encode() )
  return

def servefile(request):
  if request.path == '/':
    request.path = '/index.html'

  request.path = 'webclient%s' % request.path

  if os.path.isfile( request.path ):
    request.send_response_only(200)
    request.end_headers()
    with open( request.path, mode='rb' ) as fp:
      request.wfile.write( fp.read() )
    return

  request.send_response_only(404)
  request.end_headers()
  return

def POSTsetscene( request ):
  postdata = request.rfile.read(int(request.headers['content-length']))
  try:
    parsed = json.loads( postdata.decode() )
  except json.decoder.JSONDecodeError:
    request.send_response_only(500)
    request.end_headers()
    request.wfile.write( 'Could not parse JSON data'.encode() )
    return

  with open('scenes.json', mode='r') as fp:
    scenes = json.load( fp )

  nodescenes = scenes[ parsed[ 'node' ] ]
  if not parsed['scene'] in nodescenes:
    request.send_response_only(500)
    request.end_headers()
    request.wfile.write( 'Supplied scene is not available for node'.encode() )
    return

  nodes = getBeacons()
  try: 
    node = nodes[ parsed[ 'node' ] ]
  except KeyError:
    request.send_response_only(500)
    request.end_headers()
    request.wfile.write( 'Supplied node has not checked in'.encode() )
    return

  pixelvalues = parsepayload( nodescenes[parsed['scene']] )
  binaryvalue = buildpayload( parsed[ 'node' ], pixelvalues )

  result = sendTCP( node[ 'ip_address' ], node[ 'tcp_port' ], binaryvalue )
  result = int.from_bytes( result, byteorder='big', signed=False )

  request.send_response_only( 200 )
  request.end_headers()
  request.wfile.write( ('%d' % result).encode() )
  return

def parsepayload( lightranges ):
  alldata = {}
  for lightrange in lightranges:
    for pixelpos in range(lightrange['first'], lightrange['last']+1):
      alldata[pixelpos] = [lightrange['color'][0], lightrange['color'][1], lightrange['color'][2]]

  return alldata

def buildpayload( macaddress, pixelvalues ):
  payload = binascii.unhexlify( macaddress )
  for key in pixelvalues.keys():
    payload = payload + struct.pack("!BBBB", key, pixelvalues[key][0], pixelvalues[key][1], pixelvalues[key][2])

  return payload

def sendTCPasync( ip, port, payload ):
  sendthread = threading.Thread( target=sendTCP, daemon=True, args=( ip, port, payload ) )
  sendthread.run()
  return

def sendTCP( ip, port, payload ):
  connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  connection.settimeout(1)
  connection.connect((ip, port))
  connection.send(payload)
  response = connection.recv(1024)
  connection.close()

  return response
