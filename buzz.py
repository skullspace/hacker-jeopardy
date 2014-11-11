#!/usr/bin/env python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Mark Jenkins <mark@markjenkins.ca>
# @author Jay Smith <jayvsmith@gmail.com>

import socket, ConfigParser

Config = ConfigParser.ConfigParser()
Config.read("config.ini")

HOST = Config.get("buzzer", "server_ip")
PORT = Config.getint("buzzer", "udp_port")

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def buzz(buzz_number):
    try:
        s.sendto(str(buzz_number), (HOST, PORT))
    except IOError:
        pass

if __name__ == "__main__":
    from sys import argv
    buzz(int(argv[1]))
