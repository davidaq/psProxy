import socket, sys, select, SocketServer, time, threading, os
from common import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(self, sock, remote):
		while True:
			r, w, e = select.select([sock, remote], [], []);
			if sock in r:
				if remote.send(decodeRecv(sock, 4096)) <= 0:
					break
			if remote in r:
				if encodeSend(sock, remote.recv(4096)) <= 0:
					break
	def handle(self):
		try:
			print 'Socks connection from ', self.client_address 
			
			# The Socks5 is partly moved to client
			sock = self.request
#			while True:
#				header = decodeRecv(sock)
#				print "Sending back: " + header
#				encodeSend(sock, header)
#			return
			#1. Version
			#data = decodeRecv(sock, 262); # Header
			#encodeSend(sock, b"\x05\x00");
			#2. Request
			data = decodeRecv(sock, 4)	#Maybe unsafe
			mode = ord(data[1])
			addrtype = ord(data[3])
			if addrtype == 1:		#IPV4
				addr = socket.inet_ntoa(decodeRecv(sock, 4));
			elif addrtype == 3: 	#Domain
				addr = decodeRecv(sock, ord(decodeRecv(sock, 1)[0]))
			port = struct.unpack('>H', decodeRecv(sock, 2))[0]
			reply = b"\x05\x00\x00\x01"
			print 'Request to ' + addr + '\t Port: ' + str(port)
			try:
				if mode == 1: #1. Connection mode
					remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					remote.connect((addr, port))
				else:
					reply = b"\x05\x07\x00\x01"
				local = remote.getsockname()
				reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
			except socket.error:
				print 'Connection refused'
				sock.close()
				return
			encodeSend(sock, reply)
			#3. Tranfer!!
			if reply[1] == '\x00':
				if mode == 1: #1. connection mode
					self.handle_transfer(sock, remote)
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
def main():
	server = ThreadingTCPServer(('', 5060), ProxyServer)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = False
	server_thread.start()
#	while True:
#		pass
#		tmp = raw_input(">>> ")
#		if tmp == 'shutdown':
#			server.shutdown()
#			return
if __name__ == '__main__':
	main()
