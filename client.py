#!/usr/bin/python
import socket, sys, select, SocketServer, time, threading, os, traceback
from common import *		# Including public function
from resources import * 	# Including remotelist and fakeiplist
desirelist={}
iplist = {}
userlist = {}
#Semaphore variable
sema_desire = threading.BoundedSemaphore(1)
sema_ip = threading.BoundedSemaphore(1)
sema_user = threading.BoundedSemaphore(1)
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class ProxyServer(SocketServer.StreamRequestHandler):
	def check_remote(self, linkinfo, sockshead, links):
		try:
			remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			remote.settimeout(2)  # 2 seconds
			remote.connect(linkinfo)
			encodeSend(remote, sockshead)	#Resend head
			reply = decodeRecv(remote, 4)
			if reply[1] != '\x00':
				remote.close()
				return [False, reply, ""]
			addrtype = ord(reply[3])
			if addrtype == 1:		#IPV4
				nextLen = 4
			elif addrtype == 3: 	#Domain
				nextLen = ord(decodeRecv(remote, 1)[0])
			nextLen += 2	#For port
			reply += decodeRecv(remote,nextLen)
			
			#Get ip!! (not a part of socks5 protocol)
			ip = socket.inet_ntoa(decodeRecv(remote, 4))
			
			if len(reply) == nextLen + 4 and ip not in fakeip:
				links.append(remote)
				remote.settimeout(10)
				return [True, reply, ip]
			if ip in fakeip:
				print "Fake ip:" , ip
		except socket.error, msg:
			pass
			#print "Error in check_remote: ", msg, "to: ", linkinfo
		remote.close()
		return [False, "", ""]
	def handle_transfer(self, sock, links, ip):
		global desirelist, sema_desire
		links.append(sock)	#Put browser socket into links
		flag = True
		cnt = 0	#For reconnect
		while len(links) > 0 and (flag or cnt < 10):
			if not flag: cnt += 1
			else:	cnt = 0;
			r, w, e = select.select(links, [], [], 0.5);
			# forward to all active remote links
			flag = False
			try:
				for link in r:
					if link is sock:	#Browser socket -- only one
						data = sock.recv(4096)
						if len(data)  == 0:
							links.remove(sock)
							break
						for l in [x for x in links if x != sock]:
							encodeSend(l, data)
						flag = True
					else:				#Server socket
						if sock.send(decodeRecv(link, 4096)) <= 0: #Data == 0?
							#link.close()
							links.remove(link)
							break
						#Close all server sockets except the ont first responced.
						for l in [x for x in links if x != sock and x != link]:
							#l.close()
							if l in r: r.remove(l)
							if l in links: links.remove(l)
						sema_desire.acquire()	#Semaphore, update desirelist
						desirelist[ip] = [time.time() + 2 * 3600, link.getpeername()]
						sema_desire.release()
						flag = True
			except socket.error, msg:
				flag = False
				#print "Interrupted while transfering: ", msg
		#Close all connection
		for link in links: link.close()
		sock.close()
			
	def handle(self):
		global desirelist,remoteList, iplist, userlist
		global sema_ip, sema_desire, sema_user
		try:
			#print "Number of threads: ", threading.activeCount()
			sema_user.acquire()
			if self.client_address[0] not in userlist:
				print 'New connection from ', self.client_address 
				userlist[self.client_address[0]] = 1
			sema_user.release()
			
			sock = self.request			
			sock.recv(262)
			sock.send(b"\x05\x00")
			time.sleep(0.1)
			data = sock.recv(4)
			socksHead = data
			mode = ord(data[1])
			addrtype = ord(data[3])
			if addrtype == 1:		#IPV4
				data = sock.recv(4); socksHead += data
				addr = socket.inet_ntoa(data)
			elif addrtype == 3: 	#Domain
				data = sock.recv(1); socksHead += data
				addr = sock.recv(ord(data[0])); socksHead += addr
			socksHead += sock.recv(2); #Port
			
			# Update desire list if exist and expire
			links=[]
			if (addr in iplist and 
				iplist[addr] in desirelist and 
				desirelist[iplist[addr]][0] > time.time()):
				flag, reply, ip = self.check_remote(desirelist[iplist[addr]][1],
				 socksHead, links)
			# Create desire list
			failed = 0
			while len(links) == 0 and failed < 5:
				failed += 1
				for linkinfo in remoteList:
					flag, ret, ip = self.check_remote(linkinfo[0], socksHead, links)
					if flag: 	#Server support this protocol
						reply = ret
						sema_ip.acquire()
						if addr not in iplist:
							iplist[addr] = ip
						sema_ip.release()
			if len(links) == 0:
				print 'No usable remote proxy for ' + addr
				sock.close()
				return
			# Global check
			sock.send(reply)
			self.handle_transfer(sock, links, iplist[addr]) #Start transfering
		except socket.error, msg:
			pass
			#print 'Socket Error in handle(): ', msg
		except Exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print "Other Exception: "
			traceback.print_exception(exc_type, exc_value, exc_traceback,
			                              limit=2, file=sys.stdout)
def main():
	try:
#		for i in xrange(len(remoteList) - 1, -1, -1):
#			if not hostalive(remoteList[i][0]):
#				remoteList.remove(remoteList[i])
#		if len(remoteList) == 0:
#			print "No available server, I'm dead now"
#			return
		print "Check remote list done, start listening..."
		threading.stack_size(1024 * 512)
		server = ThreadingTCPServer(('', 5070), ProxyServer)
		server_thread = threading.Thread(target=server.serve_forever)
		server_thread.start()
	except Exception, msg:
		print "Exception in main: " , msg
if __name__ == '__main__':
	main()
