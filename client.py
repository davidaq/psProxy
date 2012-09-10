import socket, sys, select, SocketServer, time, threading, os
from common2 import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(self, sock, remote):
		while True:
			r, w, e = select.select([sock, remote], [], []);
			if sock in r:
				data = sock.recv(4096)
				#print 'Data sent to remote: ' + data
				if encodeSend(remote, data) <= 0:
					break
			if remote in r:
				data = decodeRecv(remote, 4096)
				#print 'Data received from remote:' + data
				if sock.send(data) <= 0:
					break
	def handle(self):
		try:
			print 'In comming connection from ', self.client_address 
			sock = self.request
			try:
				remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				remote.connect(("127.0.0.1", 5060))
			except socket.error:
				print 'Connection refused'
			self.handle_transfer(sock, remote)
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
def main():
	server = ThreadingTCPServer(('', 5070), ProxyServer)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	while True:
		tmp = raw_input(">>> ")
		if tmp == 'shutdown' or tmp == 'close':
			server.shutdown()
			return
if __name__ == '__main__':
	main()