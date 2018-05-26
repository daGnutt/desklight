#!/usr/bin/env python3

"""runtime.py: The runtime to start to run the desk lighting system."""

__author__ = "Gnutt Halvordsson"

import listener
import time
import webhandler
import webserver

def __main():
    checkin = listener.listener('', 5007)
    checkin.verbose = False

    webinterface = webserver.GServer( '', 5009, webhandler.do_GET, webhandler.do_POST )
    print( "Starting Checkin Server" )
    checkin.start()

    print( "Starting Web Interface" )
    webinterface.startserverasync()

    print( "All Services started. Going to display mode" )

    while True:
        time.sleep(10)
        print(checkin.get_beacons())
        pass


if __name__ == '__main__':
    __main()
