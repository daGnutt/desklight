#!/usr/bin/env python3

"""runtime.py: The runtime to start to run the desk lighting system."""

__author__ = "Gnutt Halvordsson"

import listener
import time

def __main():
    checkin = listener.listener('', 5007)
    checkin.verbose = True

    print("Starting Checkin Server")
    checkin.start()
    print("Server Started... Going to display mode")

    while True:
        time.sleep(1)
        print(checkin.get_beacons())
        pass


if __name__ == '__main__':
    __main()
