import socket as S
import threading as T
from common import *

#some settings
tsInfo = ('172.28.11.175',5050)
PORT = 5080


lS=0
CLOSE=False
map=[]
def returnThread(tS,sc):
	tS.settimeout(10)
	while not CLOSE:
		try:
			buff=decodeRecv(tS,8)
		except:
			pass
		print '<' ,buff
		if not buff:
			print 'end'
			break
		sc.send(buff)
	tS.close()
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
		print '>' ,buff
		encodeSend(tS,buff,8)
	
def acceptThread(lS):
	'''Accpet a connection'''
	while not CLOSE:
		try:
			(sc,addr)=lS.accept()
		except:
			continue
		sT=T.Thread(target=serveThread,args=(sc,addr))
		sT.start()
	lS.close()
def begin(PORT,LIMIT,TIMEOUT):
	'''Start the listening procces'''
	global lS
	lS=S.socket(S.AF_INET,S.SOCK_STREAM)
	lS.settimeout(TIMEOUT)
	lS.bind(('127.0.0.1',PORT))
	lS.listen(LIMIT)
	aT=T.Thread(target=acceptThread,args=(lS,))
	aT.start()
		
begin(PORT,10,1)
while not CLOSE:
	cmd=raw_input(">")
	if(cmd=="help"):
		print ''''''
	elif(cmd=="close"):
		CLOSE=True
