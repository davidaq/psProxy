#!/usr/bin/python
import socket
import struct
import threading
import select
import SocketServer
from securesocket import *
from const import *
from common import *

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass

class Socks5Client(SocketServer.StreamRequestHandler):

	def connect_remote(self, id, addr, result):
		result[id] = create_socket(addr, secure=True)

	def asyn_do(self, target, args):
		for i in xrange(self.cnt):
			self.threads[i] = threading.Thread(target=target, args=eval(args))
			self.threads[i].start()
		self.wait_threads()
		
	def wait_threads(self):
		for i in xrange(len(self.threads)):
			if self.threads[i]:
				self.threads[i].join()

	def auth(self, id, data, result):
		if not self.remote[id]: return
		self.remote[id].sendall(data)
		result[id] = self.remote[id].recvall(2)
		'''
		print "Auth send:",
		printbytes(data)
		print "Auth recv:",
		printbytes(result[id])
		'''

	def handle_request(self, id, data, result):
		if not self.remote[id]: return
		self.remote[id].sendall(data)
		result[id] = self.remote[id].recvall(4)
		if result[id][1] == b'\x00':
			result[id] += self.remote[id].recvall(6)
		'''
		print "Req send:", 
		printbytes(data) 
		print "Req recv:",
		printbytes(result[id])
		'''

	def close_one_remote(self, i):
		if self.remote[i]:
			self.remote[i].close()
		self.remote[i] = None

	def evaluate_result(self, errormsg):
		ret = (False, "")
		for i in xrange(len(self.result)):
			if self.result[i] and ord(self.result[i][1]) == 0:
				ret = (True, self.result[i])
			else:
				self.close_one_remote(i)
		if ret[0]:
			self.client.sendall(ret[1])
		else:
			raise Exception(errormsg)

	def transfer(self):
		while True:
			links = [self.client] +  self.remote
			try:
				r, w, e = select.select(links, [], [], 300);
			except Exception as e: 
				print "Select: ", e
				break	
			if len(r) == 0 or len(self.remote) == 0: return
			if self.client in r:
				data = self.client.recv(4096)
				if not data: return
				for i in self.remote:
					i.send(data)
			for i in xrange(len(self.remote) - 1, -1, -1):
				if self.remote[i] in r:
					data = self.remote[i].recv(4096)
					if not data: 
						self.remote[i].close()
						self.remote.remove(self.remote[i])
						continue
					for j in xrange(len(self.remote)):
						if i != j:
							self.remote[j].close()
					self.remote = [self.remote[i]]
					self.client.send(data) 
					break

	def update(self):
		for i in xrange(self.cnt - 1, -1, -1):
			if not self.remote[i]:
				self.remote.remove(self.remote[i])
				self.threads.remove(self.threads[i])
				self.cnt -= 1
	
	def handle(self):
		try:
			self.client = SecureSocket(sock=self.request, secure=False)
			self.cnt = len(serverlist)
			self.remote = [None for i in xrange(self.cnt)]
			self.threads = [None for i in xrange(self.cnt)] 

			#Build connection with servers
			self.asyn_do(self.connect_remote, "(i, serverlist[i], self.remote)")
			self.update()

			if self.cnt == 0:
				print "No server available"
				return

			#1.Version
			self.data = self.client.recvall(2)
			self.data += self.client.recv(ord(self.data[1]))
			self.result = [None for i in xrange(self.cnt)]
			self.asyn_do(self.auth, "(i, self.data, self.result)") 
			self.evaluate_result("Auth failed")
			self.update()

			#2.Request
			self.data = self.client.recvall(4)
			self.result = [None for i in xrange(self.cnt)]
			atyp = ord(self.data[3])
			if atyp == 1:
				self.data += self.client.recvall(4)
			elif atyp == 3:
				alen = self.client.recvall(1)
				self.data += alen
				self.data += self.client.recvall(ord(alen[0]))
			self.data += self.client.recvall(2)
			self.asyn_do(self.handle_request, "(i, self.data, self.result)") 
			self.evaluate_result("handle request failed")
			self.update()
			
			#3.Transfer
			self.transfer()
			
		except Exception as e:
			printexc()
		finally:
			self.client.close()
			for s in self.remote:
				if s:
					s.close()

def main():
	try:
		print "Start listening..."
		threading.stack_size(1024 * 512 * 2)
		socket.setdefaulttimeout(30)
		server = ThreadingTCPServer(('', 5070), Socks5Client)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception, msg:
		print "Exception in main: ", msg
if __name__ == '__main__':
	main()
