#!/usr/bin/env python3

"""listener.py: A checkin server for desk lighting beacons"""

__author__ = "Gnutt Halvordsson"

import binascii
import socket
import struct
import threading
import time

class listener:
    verbose = False
    def __init__(self, serverip, serverport):
        self.__serverip = serverip
        self.__serverport = serverport
        self.__beacons = {}
        self.___verbose = False

    def start(self):
        self.__startasyncserver()
        self.__startcheckstale()

    def get_beacons(self):
        return self.__beacons

    def __startcheckstale(self):
        stale_thread = threading.Thread(
            name='StaleChecker', target=self.__checkstale, daemon=True
        )
        stale_thread.start()

    def __checkstale(self):
        while True:
            now = time.time()
            for mac in self.__beacons:
                beacon = self.__beacons[mac]
                since_seen = now - beacon['last_seen']
                if since_seen > 30 and beacon[mac]['active']:
                    if self.verbose:
                        print("Beacon %s became inactive" % binascii.hexlify(mac))
                    beacon['active'] = False

                if since_seen > 60*5:
                    if self.verbose:
                        print("Beacon %s considered dead" % binascii.hexlify(mac))
                    del(beacon)
            time.sleep(10)

    def __startasyncserver(self):
        udp_thread = threading.Thread(
            name='UDPserver', target=self.__startsyncserver, daemon=True)
        udp_thread.start()

    def __startsyncserver(self):
        udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_server.bind((self.__serverip, self.__serverport))
        while True:
            data, address = udp_server.recvfrom(4096)
            self.__handlecheckin(data, address)

    def __handlecheckin(self, data, sender):
        if self.verbose:
            print("Parsing Data")
        try:
            (beacontype, macaddress, tcp_port) = struct.unpack(">2s6sH", data)
        except struct.error:
            if self.verbose:
                print("Bad Data from %s:%s" % (sender[0], sender[1]))
                print(binascii.hexlify(data))
            return False

        if beacontype != b'DL':
            if self.verbose:
                print("Wrong Beacontype")
            return False

        if not macaddress in self.__beacons:
            self.__beacons[macaddress] = {}

        self.__beacons[macaddress].update({
            "last_seen": int(time.time()),
            "ip_address": sender[0],
            "tcp_port": tcp_port,
            "active": True
        })

        if self.verbose:
            print(binascii.hexlify(data))
            print(sender)
        return True
