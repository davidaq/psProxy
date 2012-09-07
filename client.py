import socket as S
import threading as T

lS=0
tS=0
tsInfo = ('',3333)
def serveThread(sc,addr):
	'''Serve the connected client'''
	sc.settimeout(0.1)
	data=''
	tsInfo
	while True:
		buff=sc.recv(1024)
		if not buff:
			break
		data+=buff
	
def acceptThread(lS):
	'''Accpet a connection'''
	while True:
		try:
			(sc,addr)=lS.accept()
		except:
			continue
		sT=T.Thread(target=serveThread,args=(sc,addr))
		sT.start()
def begin(PORT,LIMIT,TIMEOUT):
	'''Start the listening procces'''
	global lS
	global tS
	tS=S.socket(S.AF_INET,S.SOCK_STREAM)
	lS=S.socket(S.AF_INET,S.SOCK_STREAM)
	lS.settimeout(TIMEOUT)
	lS.bind(('127.0.0.1',PORT))
	lS.listen(LIMIT)
	aT=T.Thread(target=acceptThread,args=(lS,))
	aT.start()
		
begin(8080,10,10)
