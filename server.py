import socket, sys, select, SocketServer, time, threading, os
from common import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def __init__(self, request, client_addr, server):
		self.debug = False	#Debug mode
		SocketServer.StreamRequestHandler.__init__(self, request, client_addr, server)
	def handle_transfer(self, sock, remote):
		while True:
			r, w, e = select.select([sock, remote], [], []);
			if sock in r:
				if remote.send(decodeRecv(sock)) <= 0:
					break
			if remote in r:
				data = remote.recv(4096)
				#print "Received from client: " + data
				if encodeSend(sock, data) <= 0:
					break
	def handle(self):
		try:
			print 'In comming connection from ', self.client_address 
			sock = self.request
			if self.debug:
				while True:
					header = decodeRecv(sock)
					print "Sending back: " + header
					encodeSend(sock, header)
				return
			header = decodeRecv(sock)
			while '\n' not in header:
				header += decodeRecv(sock)
			(verb, url, version) = header[0 : header.find('\n')].split()
			if verb == 'CONNECT':
				(url, port) = url.split(':')
			else:
				url = url.split('/')[2]
				if ':' in url:
					(url, port) = url.split(':')
				else:
					port = '80'
			print "Client requsted to " + url + " Port:" + port
			try:
				remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				remote.connect((url, int(port)))
			except socket.error:
				print 'Connection refused'
			remote.send(header)
			self.handle_transfer(sock, remote)
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
def main():
	server = ThreadingTCPServer(('', 5060), ProxyServer)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	while True:
		tmp = raw_input(">>> ")
		if tmp == 'shutdown':
			server.shutdown()
			return
if __name__ == '__main__':
	main()