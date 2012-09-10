import socket, struct

def decodeRecv(sock):
	head = sock.recv(4)
	if head == '': return ''
	l = struct.unpack('>i', head)[0]
	data = list(sock.recv(l))
	for i in reversed(xrange(l - 1)):
		data[i] = chr(ord(data[i]) ^ ord(data[i + 1]))
	return ''.join(data)
def encodeSend(sock, data):
	data = list(data)
	l = len(data)
	for i in xrange(l - 1):
		data[i] = chr(ord(data[i]) ^ ord(data[i + 1]))
	return sock.send(struct.pack('>i', len(data)) + ''.join(data))
