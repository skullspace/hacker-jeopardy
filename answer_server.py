# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Jay Smith <jayvsmith@gmail.com>

import threading, ConfigParser
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class _AnswerRequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('content_type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write(self.server.current_answer)

    def log_message(self, format, *args):
        return

class _AnswerServer(HTTPServer):
    def __init__(self, port):
        HTTPServer.__init__(self, ('',port), _AnswerRequestHandler)
        self.current_answer = "None Yet"

    def serve_answers(self):
        threading.Thread(target=self.serve_forever).start()

class _DisabledAnswerServer(object):
    #Stub class that does nothing
    def serve_answers(self):
        return
    def shutdown(self):
        return

def build_answer_server():
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    enabled = config.getboolean("answer server", "enabled")
    port = config.getint("answer server", "tcp_port")

    if enabled:
        return _AnswerServer(port)
    else:
        return _DisabledAnswerServer()
