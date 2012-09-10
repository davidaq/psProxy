import socket, struct
swap = lambda data: chr((((ord(data) & 240) >> 4) | (ord(data) << 4)) & 255)
def decodeRecv(sock, num = 4096):
	data = list(sock.recv(num))
	data = map(swap, data)
	return ''.join(data)
def encodeSend(sock, data):
	data = list(data)
	data = map(swap, data)
	return sock.send(''.join(data))
def printDataInt(data):
	for i in data:
		print str(ord(i)) + " ",
	print ""
	