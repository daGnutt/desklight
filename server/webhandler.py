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
        get_nodes(request)
        return

    servefile(request)
    return

def do_post(request):
    """Parses and handles all POST-requests"""
    if request.path == '/setlight':
        post_setlight(request)
        return

    if request.path == '/lightoff':
        post_lightoff(request)
        return

    if request.path == '/lighton':
        post_lighton(request)
        return

    send_response(request, 500, 'NOT IMPLEMENTED')

def get_nodes(request):
    """Retrives beacons from the callback getBeacons and sends it to the api client"""
    send_response(request, 200, json.dumps(GET_BEACONS())) #pylint: disable=E1102
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

def post_setlight(request):
    """Sets the lights to the supplied color"""
    postdata = request.rfile.read(int(request.headers['content-length']))
    try:
        parsed = json.loads(postdata.decode())
    except json.decoder.JSONDecodeError:
        send_response(request, 500, "Could not parse incoming JSON data.")
        return

    nodes = GET_BEACONS() #pylint: disable=E1102
    try:
        node = nodes[parsed['node']]
    except KeyError:
        send_response(request, 500, 'Supplied node has not checked in.')
        return

    pixelvalues = {}
    for i in range(0, 180):
        pixelvalues[i] = [parsed['r'],parsed['g'],parsed['b']]

    node['pixels'] = [parsed['r'],parsed['g'],parsed['b']]
    node['brightness'] = parsed['brightness']

    payload = buildpayload(parsed['node'], pixelvalues)
    result = send_tcp(node['ip_address'], node['tcp_port'], payload)
    resultcode = int.from_bytes(result, byteorder='big', signed=False)
    send_response(request, 200, '%d' % resultcode)
    return

def post_lightoff(request):
    postdata = request.rfile.read(int(request.headers['content-length']))
    try:
        parsed = json.loads(postdata.decode())
    except json.decoder.JSONDecodeError:
        send_response(request, 500, "Could not parse incoming JSON data.")
        return

    nodes = GET_BEACONS() #pylint: disable=E1102
    try:
        node = nodes[parsed['node']]
    except KeyError:
        send_response(request, 500, 'Supplied node has not checked in.')
        return    
    
    pixelvalues = {}
    for i in range(0, 180):
        pixelvalues[i] = [0,0,0]

    payload = buildpayload(parsed['node'], pixelvalues)
    result = send_tcp(node['ip_address'], node['tcp_port'], payload)
    resultcode = int.from_bytes(result, byteorder='big', signed=False)
    send_response(request, 200, '%d' % resultcode)
    return

def post_lighton(request):
    postdata = request.rfile.read(int(request.headers['content-length']))
    try:
        parsed = json.loads(postdata.decode())
    except json.decoder.JSONDecodeError:
        send_response(request, 500, "Could not parse incoming JSON data.")
        return

    nodes = GET_BEACONS() #pylint: disable=E1102
    try:
        node = nodes[parsed['node']]
    except KeyError:
        send_response(request, 500, 'Supplied node has not checked in.')
        return
    
    pixelvalues = {}
    for i in range(0, 180):
        pixelvalues[i] = node['pixels']

    payload = buildpayload(parsed['node'], pixelvalues)
    result = send_tcp(node['ip_address'], node['tcp_port'], payload)
    resultcode = int.from_bytes(result, byteorder='big', signed=False)
    send_response(request, 200, '%d' % resultcode)
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
