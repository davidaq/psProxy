import socket, sys, select, SocketServer
from common import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(sock, remote):
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
			fline = tmp[0, header.find('\n')]
			(verb, url, version) = fline.split()
			if ':' in url:
				(url, port) = url.split()
			else:
				port = '80'
			remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote.connect((url, int(port)))
			remote.encodeSend(remote, header)
			handle_transfer(sock, remote)
		except socket.error:
			print 'Socket Error: '.socket.error
def main():
	server = ThreadingTCPServer(('', 5050), ProxyServer)
	server.serve_forever()
if __name__ == '__main__':
	main()