#!/usr/bin/env python3

"""webhandler.py: """

__author__ = "Gnutt Halvordsson"

import os
import json

getBeacons = None

def do_GET(request):
  if request.path == '/nodes':
    GETBeacons(request)
    return

  servefile(request)

def do_POST(request):
  if request.path == '/sendlight':
    print("Sending light")

  if request.path == '/light_on':
    print("Lights on")

  if request.path == '/light_off':
    print("Lights off")

  request.send_response_only(500)
  request.end_headers()
  request.wfile.write('NOT IMPLEMTEND'.encode())

def GETBeacons(request):
  request.send_response_only(200)
  request.end_headers()
  data = json.dumps( getBeacons() )
  request.wfile.write( data.encode() )
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
