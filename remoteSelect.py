import socket, sys, SocketServer, time, threading, os
import select as SEL
from common import *
remoteList=(
("127.0.0.1",5060), # Localhost for single layer proxy
("184.22.246.194", 5060), # Ming's VPS
)
desireList={}
def select(sock):
	# TODO read and preserve the socks5 header and resolve the target host
	socksHead1 = sock.recv(262)
	sock.send(b"\x05\x00")
	data = sock.recv(4)
	socksHead = data
	mode = ord(data[1])
	addrtype = ord(data[3])
	addrKey = data[3]
	if addrtype == 1:		#IPV4
		nextLen = 4
		#addr = socket.inet_ntoa(decodeRecv(sock, 4));
	elif addrtype == 3: 	#Domain
		data = sock.recv(1)
		socksHead += data
		addrKey += data
		nextLen = ord(data[0])
		#addr = decodeRecv(sock, ord(decodeRecv(sock, 1)[0]))
	data = sock.recv(nextLen+2)
	socksHead += data
	addrKey += data
	remote = __select(sock,addrKey)
	if remote is False:
		return False
	encodeSend(remote,socksHead1)
	decodeRecv(remote,4)
	encodeSend(remote,socksHead)
	return remote

def __select(sock,addrKey):
	global remoteList,desireList
	# check if the address already exists in the desired list and isn't expired
	print 'Desire test'
	try:
		if desireList[addrKey][0]>time.time():
			try:
				remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				remote.connect(desireList[addrKey][1])
				return remote
			except:
				pass
	except:
		pass
	print 'Global speed test'
	testData = b'\x10\x12\x00\xFF\xEE'+addrKey
	padd = 262 - len(testData)
	while padd>0:
		padd-=1
		testData+=b'\x00'
	testList = []
	for addr in remoteList:
		try:
			remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			remote.settimeout(2)
			remote.connect(addr)
			if encodeSend(remote,testData)>0:
				testList.append(remote)
		except Exception,e:
			print 'Fail:',e
			pass
	if len(testList)==0:
		return False
	desired = False
	# get the first responding remote proxy server
	print 'Waiting for respond'
	while desired is False:
		r, w, e = SEL.select(testList, [], []);
		for l in r:
			data = l.recv(5)
			if data == b'\x10\x12\x00\xFF\xEE':
				desired = l.getpeername()
				break
	for link in testList:
		link.close()
	print 'Desirable proxy ', desired
	desireList[addrKey]=(time.time()+3600,desired)
	remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	remote.connect(desired)
	return remote
