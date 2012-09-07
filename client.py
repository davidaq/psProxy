import socket as S
import threading as T
from common import *

#some settings
tsInfo = ('172.28.11.175',5050)
PORT = 8080


lS=0
CLOSE=False
def returnThread(tS,sc):
	tS.settimeout(0.1)
	while not CLOSE:
		try:
			buff=decodeRecv(tS,8)
		except:
			break
		if not buff:
			break
		sc.send(buff)
	sc.close()
def serveThread(sc,addr):
	'''Serve the connected client'''
	sc.settimeout(0.02)
	tS=S.socket(S.AF_INET,S.SOCK_STREAM)
	tS.connect(tsInfo)
	rT=T.Thread(target=returnThread,args=(tS,sc))
	rT.start()
	while not CLOSE:
		try:
			buff=sc.recv(8)
		except:
			break
		if not buff:
			break
		encodeSend(tS,buff,8)
	tS.close()
	
def acceptThread(lS):
	'''Accpet a connection'''
	while not CLOSE:
		try:
			(sc,addr)=lS.accept()
		except:
			continue
		sT=T.Thread(target=serveThread,args=(sc,addr))
		sT.start()
def begin(PORT,LIMIT,TIMEOUT):
	'''Start the listening procces'''
	global lS
	lS=S.socket(S.AF_INET,S.SOCK_STREAM)
	lS.settimeout(TIMEOUT)
	lS.bind(('127.0.0.1',PORT))
	lS.listen(LIMIT)
	aT=T.Thread(target=acceptThread,args=(lS,))
	aT.start()
		
begin(PORT,10,10)
while True:
	cmd=raw_input(">")
	if(cmd=="help"):
		print ''''''
	elif(cmd=="close"):
		CLOSE=True
