import socket, time
from common import *
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 5060))
while True:
	data = raw_input()
	if not data: break
	encodeSend(sock, data)
	data = decodeRecv(sock)
	#time.sleep(0.1)
	print data + " --- len = " + str(len(data))