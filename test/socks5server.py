#!/usr/bin/python
import socket, select, SocketServer, time, threading, os, sys
import struct
import traceback
import errno
from securesocket import *
from common import *
from const import *

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass

class Socks5Server(SocketServer.StreamRequestHandler):

	'''
	Hendle the version infomation and authentication message
	return True when success, vice versa
	'''
	def auth(self):
		data = self.client.recvall(2)
		data += self.client.recv(ord(data[1]))

		if data[0] != b'\x05': # Not SOCKS 5 protocol, close connection
			self.client.send(b'\x05\xFF')
			return False
		self.client.sendall(b'\x05\x00')
		return True
			
		'''
		ulen = ord(self.client.recvall(2)[0]) # Including version info
		uname = self.client.recvall(ulen)
		plen = ord(self.client.recvall(1)[0])
		passwd = self.client.recvall(plen)
		
		# Check the password and username
		if uname == "ming" and passwd == "ming":
			self.client.send("\x00")
			return True
		else:
			self.client.send("\x01")
			return False
		'''

	'''
	Handle the protocol request from client.
	'''
	def handle_request(self):
		data = self.client.recvall(4) # The SOCKS protocol was not designed very well I think
		cmd = ord(data[1])
		atyp = ord(data[3])
		reply = b"\x05"
		if atyp == 1: #IPV4
			addr = socket.inet_ntoa(self.client.recvall(4))
		elif atyp == 3: #Domain name
			addr = self.client.recvall(ord(self.client.recvall(1)[0]))
		else:	#So bad, IPV6... I dont know how to handle it.
			log("Cannot handle IPV6...")
			reply += b"\x08\x00\x01"
			self.client.sendall(reply) 
			return False
		port = struct.unpack('>H', self.client.recvall(2))[0] # Get port number

		if cmd == 1: # try to connect the request server!
			self.remote = create_socket((addr, port)) 
			if not self.remote: 
				log(("Can't connect to", addr)) 
				reply += b"\x04\x00\x01"
				self.client.sendall(reply)
				return False
			local = self.remote.getsockname()
			reply += b"\x00\x00\x01"
			reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
		else: # Not support this command currently
			log("Unsupported command here")
			reply += b"\x07\x00\x01"
			self.client.sendall(reply)
			return False

		self.client.sendall(reply)
		return True

	def transfer(self):
		self.remote.settimeout(socket.getdefaulttimeout())
		links = [self.client, self.remote]
		while True:
			try:
				r, w, e = select.select(links, [], [], 300);
			except: 
				break	
			if len(r) == 0: break
			if self.client in r:
				if self.remote.send(self.client.recv(4096)) <= 0: 
					break
			if self.remote in r:
				if self.client.send(self.remote.recv(4096)) <= 0: 
					break

	def handle(self):
		try:
			self.client = SecureSocket(sock=self.request, secure=SECURE)
			self.remote = None
			if self.auth() == False:
				raise Exception("Authentication failed")
			#print "Authentication succeeded"
			if self.handle_request() == False:
				raise Exception("Handling request failed")
			self.transfer()
		except SecureSocketError as msg:
			printexc()
		except socket.error, msg:
			printexc()
		except Exception, msg:
			printexc()
		finally:
			self.client.close()
			if self.remote: 
				self.remote.close()

def main():
	try:
		print "Start listening..."
		threading.stack_size(1024 * 512 * 2)
		socket.setdefaulttimeout(30)
		server = ThreadingTCPServer(('', 5060), Socks5Server)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception, msg:
		print "Exception in main: ", msg
if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", help="Running secure server", action = "store_true")
	args = parser.parse_args()
	if args.s:
		SECURE = True
	main()
