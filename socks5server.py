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
			print 'Request to ' + addr + ' Port: ' + str(port)
			try:
				if mode == 1: #1. Connection mode
					remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					remote.settimeout(3) # 2 second
					remote.connect((addr, port))
					local = remote.getsockname()
					reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
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
			#3. Tranfer!!
			if reply[1] == '\x00':
				if mode == 1: #1. connection mode
					remote.settimeout(10)
					self.handle_transfer(sock, remote)
			sock.close()
			remote.close()
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
		except IOError as e:
		    print "I/O error({0}): {1}".format(e.errno, e.strerror)
		except IndexError:
		    print "IndexError! OMG!!!"
		except Exception:
			print "Other exception: " , sys.exc_info()[0]
def main():
	try:
		threading.stack_size(1024 * 512)
		server = ThreadingTCPServer(('', 5060), ProxyServer)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception:
		print "Exception in main: " , sys.exc_info()[0]
if __name__ == '__main__':
	main()
