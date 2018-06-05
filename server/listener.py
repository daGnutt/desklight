#!/usr/bin/env python3

"""listener.py: A checkin server for desk lighting beacons"""

__author__ = "Gnutt Halvordsson"

import binascii
import json
import socket
import struct
import threading
import time

class Listener:
    """Listens for beacons and handles their checkin-state."""
    verbose = False
    __BEACONFILENAME = 'beacons.json'

    def __init__(self, serverip, serverport):
        self.__serverip = serverip
        self.__serverport = serverport
        self.__beacons = {}
        self.___verbose = False

        try:
            with open(self.__BEACONFILENAME, mode='r') as file_pointer:
                self.__beacons = json.load(file_pointer)
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            self.__writebeacontofile()

    def start(self):
        """Initiates the services to listen, and handle staleness"""
        self.__startasyncserver()
        self.__startcheckstale()

    def get_beacons(self):
        """Returns a dictionary of all beacons and their state"""
        return self.__beacons

    def __writebeacontofile(self):
        """Stores the beacons as a file."""
        with open(self.__BEACONFILENAME, mode='w') as file_pointer:
            json.dump(self.__beacons, file_pointer)

    def __startcheckstale(self):
        stale_thread = threading.Thread(
            name='StaleChecker',
            target=self.__checkstale,
            daemon=True
        )
        stale_thread.start()

    def __checkstale(self):
        while True:
            now = time.time()
            for mac in self.__beacons:
                beacon = self.__beacons[mac]
                since_seen = now - beacon['last_seen']
                if since_seen > 30 and beacon['active']:
                    if self.verbose:
                        print("Beacon %s became inactive" % binascii.hexlify(mac))
                    beacon['active'] = False

                if since_seen > 60*5:
                    if self.verbose:
                        print("Beacon %s considered dead" % binascii.hexlify(mac))
                    del beacon
            time.sleep(10)

    def __startasyncserver(self):
        udp_thread = threading.Thread(
            name='UDPserver',
            target=self.__startsyncserver,
            daemon=True)
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
            (beacontype, macaddress, tcp_port, scenenumber) = struct.unpack(">2s6sHB", data)
        except struct.error:
            if self.verbose:
                print("Bad Data from %s:%s" % (sender[0], sender[1]))
                print(binascii.hexlify(data))
            return False

        if beacontype != b'DL':
            if self.verbose:
                print("Wrong Beacontype")
            return False

        macaddress = binascii.hexlify(macaddress).decode()

        if not macaddress in self.__beacons:
            self.__beacons[macaddress] = {}


        self.__beacons[macaddress].update({
            "last_seen": int(time.time()),
            "ip_address": sender[0],
            "tcp_port": tcp_port,
            "active": True,
            "scenecounter": scenenumber
        })

        if self.verbose:
            print(binascii.hexlify(data))
            print(sender)
        return True
