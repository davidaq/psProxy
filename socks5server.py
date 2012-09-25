import socket, sys, select, SocketServer, time, threading, os
from common import *
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(self, sock, remote):
		flag = True
		links = [sock, remote];
		while flag:
			r, w, e = select.select(links, [], []);
			flag = False
			if sock in r:
				data = decodeRecv(sock, 4096)
				if len(data) > 0: 
					flag = True
					if remote.send(data) <= 0: break
				else:
					links.remove(sock)
			if remote in r:
				data = remote.recv(4096)
				if len(data) > 0: 
					flag = True
					if encodeSend(sock, data) <= 0: break
				else:
					links.remove(remote)
	def handle(self):
		try:
			sock = remote = None
			#print 'Socks connection from ', self.client_address 
			# The Socks5 is partly moved to client
			sock = self.request
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
			#print 'Request to ' + addr + ' Port: ' + str(port)
			try:
				if mode == 1: #1. Connection mode
					remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					remote.settimeout(3) # 4 second
					remote.connect((addr, port))
					local = remote.getsockname()
					reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
					ip = socket.inet_aton(remote.getpeername()[0])
				else:
					reply = b"\x05\x07\x00\x01"
			except socket.error:
				print 'Connection refused or time out to ', addr
				reply = b"\x05\x07\x00\x01"
				encodeSend(sock, reply)
				sock.close()
				remote.close()
				return
			encodeSend(sock, reply)
			encodeSend(sock, ip);
			#3. Tranfer!!
			if reply[1] == '\x00':
				if mode == 1: #1. connection mode
					remote.settimeout(10)
					self.handle_transfer(sock, remote)
		except socket.error, msg:
			print 'Socket Error: ', msg
		except Exception, msg:
			print "Other exception: " , msg
		#Close
		if sock is not None: 	sock.close()
		if remote is not None: 	remote.close()
def main():
	try:
		print "Start listening..."
		threading.stack_size(1024 * 512)
		server = ThreadingTCPServer(('', 5060), ProxyServer)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception, msg:
		print "Exception in main: ", msg
if __name__ == '__main__':
	main()
