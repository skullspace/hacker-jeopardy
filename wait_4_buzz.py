#!/usr/bin/env python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Mark Jenkins <mark@markjenkins.ca>

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from buzz import PORT as BUZZ_PORT

class BuzzWaitHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # first character in the path is slash, the rest should
            # be an integer
            self.server.buzz_from = int(self.path[1:])
        # who cares about folks who don't follow the protocol
        except ValueError:
            pass
        self.send_response(200)
        self.end_headers()

def wait_4_buzz(players_allowed_to_answer):
    srvr = HTTPServer(('', BUZZ_PORT), BuzzWaitHandler)
    # keep handling requests one at a time until one of them manages
    # to set the buzz_from attribute
    while True:
        srvr.handle_request()
        if (hasattr(srvr, 'buzz_from') and
            srvr.buzz_from in players_allowed_to_answer ):
            # shutdown the server and drop everybody else in the queue
            srvr.server_close()
            return srvr.buzz_from

if __name__ == "__main__":
    while True:
        print wait_4_buzz(), "buzzed"
