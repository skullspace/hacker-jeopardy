#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep

class JeopardyServer(BaseHTTPRequestHandler):
	
	def do_GET(self):
		try:
			if self.path.endswith(".html"):
				if self.path == "/register.html":
					f = open(curdir + sep + self.path)
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
	
					return
				elif self.path == "/scores.html":
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()
					self.wfile.write("<!DOCTYPE html><head><title>SkullSpace:: Hacker Jeopardy</title><body><h1>Scores:</h1><ul>")
					scores = open('scores', 'r')
					for line in scores:
						self.wfile.write("<li>"+line+"</li>")
					self.wfile.write("</ul></body></html>")

					return
		except IOError:
			self.send_error(404, 'File Not Found: %s' % self.path)

def main():
	try:
		print 'Jeopardy Server is starting...'
		server_address = ('192.168.1.126', 80)
		httpd = HTTPServer(server_address, JeopardyServer)
		print 'Jeopardy Server is running...'
		httpd.serve_forever()
	except KeyboardInterrupt:
		print 'Shutting down server...'
		httpd.socket.close()

if __name__ == '__main__':
	main()
