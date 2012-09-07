import socket, sys, select, SocketServer
from common import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(self, sock, remote):
		while True:
			r, w, e = select.select([sock, remote], [], []);
			if sock in r:
				if encodeSend(remote, decodeRecv(sock)) <= 0:
					break
			if remote in r:
				if encodeSend(sock, decodeRecv(remote)) <= 0:
					break
	def handle(self):
		try:
			print 'In comming connection from ', self.client_address 
			sock = self.request
			header = decodeRecv(sock)
			while '\n' not in header:
				header += decodeRecv(sock)
			fline = header[0 : header.find('\n')]
			(verb, url, version) = fline.split()
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
			encodeSend(remote, header)
			self.handle_transfer(sock, remote)
		except socket.error:
			print 'Socket Error.'
def main():
	server = ThreadingTCPServer(('', 5060), ProxyServer)
	server.serve_forever()
if __name__ == '__main__':
	main()