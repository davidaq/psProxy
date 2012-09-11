# Options

remoteList=(
("127.0.0.1",5060), # Localhost for single layer proxy
("184.22.246.194", 5060), # Ming's VPS
)

# CODE

import socket, sys, select, SocketServer, time, threading, os
from common import *
desireList={}
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def handle_transfer(self, sock, links, addrKey):
		global desireList
		links.append(sock)
		print 'start handling'
		ok=True
		while ok:
			r, w, e = select.select(links, [], []);
			# forward to all active remote links
			for link in r:
				if link is sock:
					data = sock.recv(4096)
					#print 'Data sent to remote:' , data
					if data=='':
						ok = False
						break
					for l in links:
						if l is sock:
							continue
						try:
							if encodeSend(l,data)<=0:
								links.remove(l)
								l.close()
						except:
							links.remove(l)
							l.close()
				else:
					data = decodeRecv(link, 4096)
					for l in links:
						if l is sock or l is link:
							continue
						l.close()
					links=[sock,link]
					desireList[addrKey]=(time.time()+10,link.getpeername())
					#print 'Data received from remote:' , data
					if sock.send(data) <= 0:
						ok = False
						break
		for link in links:
			link.close()
	def handle(self):
		global desireList,remoteList
		try:
			print 'In comming connection from ', self.client_address 
			sock = self.request			
			sock.recv(262)
			sock.send(b"\x05\x00")
			data = sock.recv(4)
			socksHead = data
			mode = ord(data[1])
			addrtype = ord(data[3])
			addrKey = data[3]
			if addrtype == 1:		#IPV4
				nextLen = 4
			elif addrtype == 3: 	#Domain
				data = sock.recv(1)
				socksHead += data
				addrKey += data
				nextLen = ord(data[0])
			data = sock.recv(nextLen+2)
			socksHead += data
			addrKey += data
			links=[]
			# Check desirable
			try:
				if desireList[addrKey][0]>time.time():
					remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					remote.settimeout(2)
					remote.connect(desireList[addrKey][1])
					encodeSend(remote,socksHead)
					data = decodeRecv(remote,4)
					reply = data
					addrtype = ord(data[3])
					if addrtype == 1:		#IPV4
						nextLen = 4
					elif addrtype == 3: 	#Domain
						data = sock.recv(1)
						socksHead += data
						addrKey += data
						nextLen = ord(data[0])
					nextLen+=2
					data = decodeRecv(remote,nextLen)
					reply += data
					if len(data)==nextLen and reply[1]== '\x00':
						print 'Desired exists'
						links.append(remote)
					else:
						remote.close()
			except socket.error:
				print 'Connection refused'
			except:
				pass
			# Global check
			if len(links)==0:
				for item in remoteList:
					try:	
						remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
						remote.settimeout(2)
						print 'Try',item
						remote.connect(item)
						encodeSend(remote,socksHead)
						data = decodeRecv(remote,4)
						reply = data
						addrtype = ord(data[3])
						if addrtype == 1:		#IPV4
							nextLen = 4
						elif addrtype == 3: 	#Domain
							data = sock.recv(1)
							socksHead += data
							addrKey += data
							nextLen = ord(data[0])
						nextLen+=2
						data = decodeRecv(remote,nextLen)
						reply += data
						if len(data)==nextLen and reply[1]== '\x00':
							links.append(remote)
						else:
							print 'Bad reply'
							remote.close()
					except Exception,e:
						print e
			if len(links)==0:
				print 'No usable remote proxy'
				sock.close()
				return
			sock.send(reply)
			self.handle_transfer(sock, links, addrKey)
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
def main():
	server = ThreadingTCPServer(('', 5070), ProxyServer)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = False
	server_thread.start()
#	while True:
#		tmp = raw_input(">>> ")
#		if tmp == 'shutdown' or tmp == 'close':
#			server.shutdown()
#			return
if __name__ == '__main__':
	main()
