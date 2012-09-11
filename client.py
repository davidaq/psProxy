# Options

remoteList=(
("184.22.246.194", 5060), # Ming's VPS
("127.0.0.1", 5060), # Localhost for single layer proxy
)

# CODE

import socket, sys, select, SocketServer, time, threading, os, traceback
from common import *
desireList={}
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def check_remote(self, linkinfo, sockshead, links):
		try:
			try:
				remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				remote.settimeout(4)  #2 second
				remote.connect(linkinfo)
			except socket.error:
				print 'Bloody unknown error!'
			encodeSend(remote, sockshead)
			time.sleep(0.1)		#In case of bloody fucking timed out
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
			if len(data) == nextLen and reply[1]== '\x00':
				links.append(remote)
				remote.settimeout(30)
				return [True, reply]
			else:
				remote.close()
		except socket.error:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print 'Socket Error in check_remote(): '
			traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
			print "link info: ", linkinfo 
			remote.close()
		return [False, " "]
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
						if encodeSend(l, data) <= 0:
							links.remove(l)
							if l in r: r.remove(l)
							l.close()
				else:
					data = decodeRecv(link, 4096)
					if len(data) == 0: 
						link.close()
						links.remove(link)
						continue
					for l in [x for x in links if x != sock and x != link]:
						l.close()
						if l in r: r.remove(l)
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
				flag, reply = self.check_remote(desireList[addrKey][1], socksHead, links)
			# Create desire list
			if len(links) == 0:
				for linkinfo in remoteList:
					flag, ret = self.check_remote(linkinfo, socksHead, links)
					if flag: reply = ret
				if len(links)==0:
					print 'No usable remote proxy!'
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
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print "Other Exception:"
			traceback.print_exception(exc_type, exc_value, exc_traceback,
			                              limit=2, file=sys.stdout)
def main():
	try:
		server = ThreadingTCPServer(('', 5070), ProxyServer)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception:
		print "Exception in main: " , sys.exc_info()[0]
if __name__ == '__main__':
	main()
