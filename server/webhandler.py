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

GET_BEACONS = None

def do_get(request):
    """Parses and handles all GET-requests"""
    parsedurl = urllib.parse.urlparse(request.path)

    if parsedurl.path == '/nodes':
        get_beacons(request)
        return

    if parsedurl.path == '/scenes':
        get_scenes(request)
        return

    servefile(request)
    return

def do_post(request):
    """Parses and handles all POST-requests"""
    if request.path == '/setscene':
        post_setscene(request)
        return
    
    if request.path == '/setbrightness':
        post_setbrightness(request)
        return

    send_response(request, 500, 'NOT IMPLEMENTED')

def get_beacons(request):
    """Retrives beacons from the callback getBeacons and sends it to the api client"""
    send_response(request, 200, json.dumps(GET_BEACONS())) #pylint: disable=E1102
    return

def get_scenes(request):
    """Reads the scenes from the JSON and returns it to the api client."""
    parsedurl = urllib.parse.urlparse(request.path)
    querystring = urllib.parse.parse_qs(parsedurl.query)

    if 'node' not in querystring:
        send_response(request, 500, 'Missing node')
        return

    with open("scenes.json", mode="r") as file_pointer:
        scenes = file_pointer.read()

    scenes = json.loads(scenes)
    if querystring['node'][0] not in scenes:
        send_response(request, 500, 'Node not found')
        return

    send_response(request, 200, json.dumps(scenes[querystring['node'][0]]))
    return

def servefile(request):
    """Servers the file that was asked for in the request."""
    if request.path == '/':
        request.path = '/index.html'

    request.path = 'webclient%s' % request.path

    if os.path.isfile(request.path):
        request.send_response_only(200)
        request.end_headers()
        with open(request.path, mode='rb') as file_pointer:
            request.wfile.write(file_pointer.read())
        return

    request.send_response_only(404)
    request.end_headers()
    return

def post_setscene(request):
    """Sends the supplied scene to the supplied node."""
    postdata = request.rfile.read(int(request.headers['content-length']))
    try:
        parsed = json.loads(postdata.decode())
    except json.decoder.JSONDecodeError:
        send_response(request, 500, 'Could not parse incoming JSON data.')
        return

    try:
        with open('scenes.json', mode='r') as file_pointer:
            scenes = json.load(file_pointer)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        send_response(request, 500, 'Could not read scenes')
        return

    nodescenes = scenes[parsed['node']]
    if not parsed['scene'] in nodescenes:
        send_response(request, 500, 'Supplied scene is not available for node.')
        return

    nodes = GET_BEACONS() #pylint: disable=E1102
    try:
        node = nodes[parsed['node']]
    except KeyError:
        send_response(request, 500, 'Supplied node has not checked in.')
        return

    pixelvalues = parsepayload(nodescenes[parsed['scene']])
    binaryvalue = buildpayload(parsed['node'], pixelvalues)

    result = send_tcp(node['ip_address'], node['tcp_port'], binaryvalue)
    result = int.from_bytes(result, byteorder='big', signed=False)

    send_response(request, 200, '%d' % result)
    return

def post_setbrightness(request):
    """Sets the brightness on the supplied node."""
    postdata = request.rfile.read(int(request.headers['content-length']))
    try:
        parsed = json.loads(postdata.decode())
    except json.decoder.JSONDecodeError:
        send_response(request, 500, 'Could not parse incoming JSON data.')
        return

    nodes = GET_BEACONS() #pylint: disable=E1102
    try:
        node = nodes[parsed['node']]
    except KeyError:
        send_response(request, 500, 'Supplied node has not checked in.')
        return
    payload  = binascii.unhexlify(parsed['node'])
    payload += b'B'
    payload += bytes([parsed['brightness']])

    print(binascii.hexlify(payload))
    result = send_tcp(node['ip_address'], node['tcp_port'], payload)
    result = int.from_bytes(result, byteorder='big', signed=False)

    send_response(request, 200, '%d' % result)
    return

def send_response(request, statuscode, message, optional_headers=None):
    """Sends a response to the request"""
    request.send_response_only(statuscode)
    if optional_headers:
        for header in optional_headers:
            request.send_header(header)
    request.end_headers()
    request.wfile.write(message.encode())

def parsepayload(lightranges):
    """Takes the data from `lightranges` and splits it into individual pixelvalues."""
    alldata = {}
    for lightrange in lightranges:
        for pixelpos in range(lightrange['first'], lightrange['last']+1):
            alldata[pixelpos] = [lightrange['color'][0],
                                 lightrange['color'][1],
                                 lightrange['color'][2]]

    return alldata

def buildpayload(macaddress, pixelvalues):
    """Generates the payload based on a macaddress and all the pixelvalues"""
    payload = binascii.unhexlify(macaddress)
    payload = payload + b'P'
    for key in pixelvalues.keys():
        payload = payload + struct.pack(
            "!BBBB",
            key,
            pixelvalues[key][0],
            pixelvalues[key][1],
            pixelvalues[key][2])

    return payload

def send_tcp_async(ip_address, port, payload):
    """Initiates a separeate deamon-thread for seding a tcp-stream"""
    sendthread = threading.Thread(target=send_tcp, daemon=True, args=(ip_address, port, payload))
    sendthread.start()
    return

def send_tcp(ip_address, port, payload):
    """Sends the supplied payload to the node"""
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(1)
    connection.connect((ip_address, port))
    connection.send(payload)
    response = connection.recv(1024)
    connection.close()

    return response
