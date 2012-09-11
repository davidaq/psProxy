# Options

remoteList=(
("184.22.246.194", 5060), # Ming's VPS
("127.0.0.1",5060), # Localhost for single layer proxy
)

# CODE

import socket, sys, select, SocketServer, time, threading, os
from common import *
desireList={}
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def check_remote(self, linkinfo, sockshead, links):
		try:
			remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			remote.settimeout(2)  #2 second
			remote.connect(linkinfo)
			encodeSend(remote, sockshead)
			data = decodeRecv(remote,4)
			reply = data
			addrtype = ord(data[3])
			if addrtype == 1:		#IPV4
				nextLen = 4
			elif addrtype == 3: 	#Domain
				nextLen = ord(decodeRecv(remote, 1)[0])
			nextLen += 2	#For port
			data = decodeRecv(remote,nextLen)
			reply += data
			if len(data)==nextLen and reply[1]== '\x00':
				links.append(remote)
			else:
				remote.close()
			return reply
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
	def handle_transfer(self, sock, links, addrKey):
		global desireList
		links.append(sock)
		#print 'Start handling....'
		ok=True
		while ok:
			r, w, e = select.select(links, [], []);
			# forward to all active remote links
			for link in r:
				if link is sock:
					data = sock.recv(4096)
					if data=='':
						ok = False
						break
					for l in [x for x in links if x != sock]:
						if encodeSend(l,data) <= 0:
							links.remove(l)
							l.close()
				else:
					data = decodeRecv(link, 4096)
					for l in [x for x in links if x != sock and x != link]:
						l.close()
					links= [sock, link]
					desireList[addrKey] = (time.time() + 1200, link.getpeername())
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
			if addrtype == 1:		#IPV4
				nextLen = 4
			elif addrtype == 3: 	#Domain
				data = sock.recv(1)
				socksHead += data
				#addrKey += data
				nextLen = ord(data[0])
			data = sock.recv(nextLen+2)
			socksHead += data
			addrKey = data
			links=[]
			# Update desire list
			if addrKey in desireList and desireList[addrKey][0] > time.time():
				reply = self.check_remote(desireList[addrKey][1], socksHead, links)
			# Create desire list
			if len(links) == 0:
				for linkinfo in remoteList:
					reply = self.check_remote(linkinfo, socksHead, links)
				if len(links)==0:
					print 'No usable remote proxy'
					sock.close()
					return
			# Global check
			sock.send(reply)
			self.handle_transfer(sock, links, addrKey)
		except socket.error, msg:
			print 'Socket Error: ' + os.strerror(msg[0])
		except IOError as e:
		    print "I/O error({0}): {1}".format(e.errno, e.strerror)
		except IndexError:
		    print "IndexError! OMG!!!"
		except Exception:
			print "Other exception: " , sys.exc_info()[0]
def main():
	server = ThreadingTCPServer(('', 5070), ProxyServer)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.start()
if __name__ == '__main__':
	main()
