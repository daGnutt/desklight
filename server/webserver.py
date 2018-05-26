#!/usr/bin/env python3

"""webserver.py: """

__author__ = "Gnutt Halvordsson"

import http.server
import threading
import time

class GServer:
    __callback = {}
    __handler = None

    def __init__(self, ip_address, port_number, get_handle, post_handle):
        self.__server_ip = ip_address
        self.__server_port = port_number
        self.__callback['GET'] = get_handle
        self.__callback['POST'] = post_handle

    def set_Callback(self, method, function):
          self.__callback[method] = function

    def startserverasync(self):
      webserverthread = threading.Thread(target=self.start_server, daemon=True)
      webserverthread.start()

    def start_server(self):
          self.__handler = http.server.BaseHTTPRequestHandler
          self.__handler.do_GET = self.__callback['GET']
          self.__handler.do_POST = self.__callback['POST']
          self.__server = http.server.HTTPServer((self.__server_ip, self.__server_port), self.__handler)
          self.__server.serve_forever()


def GET(request):
    request.send_response(200)
    request.end_headers()
    request.wfile.write('OK'.encode())
    print(request)

def __main():
    server = GServer('', 5009, GET, GET)
    server.startserverasync()
    print("Server started, waiting 5 seconds")
    time.sleep(5)
    print("Shutting down")


if __name__ == '__main__':
    __main()
