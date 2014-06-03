#!/usr/bin/python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Mark Jenkins <mark@markjenkins.ca>


from urllib import urlopen
from sys import argv

def main():
    HOST = "localhost"
    PORT = 8000

    buzz_number = int(argv[1])

    while True:
        raw_input("> ")
        try:
            urlopen("http://%s:%s/%s" % (HOST, PORT, buzz_number) )
        except IOError:
            pass

if __name__ == "__main__":
    main()
