#!/usr/bin/env python3

"""runtime.py: The runtime to start to run the desk lighting system."""

__author__ = "Gnutt Halvordsson"

import time

import listener
import webhandler
import webserver

def __main():
    checkin = listener.Listener('', 5007)
    checkin.verbose = False
    print('Starting Checkin Server')
    checkin.start()

    webhandler.GET_BEACONS = checkin.get_beacons
    webinterface = webserver.GServer('', 5009, webhandler.do_get, webhandler.do_post)

    print("Starting Web Interface")
    webinterface.startserverasync()

    print("All Services started. Going to display mode")

    while True:
        time.sleep(10)
        print(checkin.get_beacons())

if __name__ == '__main__':
    __main()
