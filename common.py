import socket
def decodeRecv(sock, num = 8):
	data = sock.recv(num)
	i = num - 2
	while i >= 0:
		data[i] = data[i] ^ data[i + 1]
	return data
def encodeSend(sock, data, num = 8):
	l = len(data)
	for i in xrange(l, num):
		for j in xrange(i, i + num):
			if j == l - 1:
				pass
			elif j >= l:
				data[j] = 0
			else:
				data[j] = data[j] ^ data[j + 1];
	return sock.send(data)
			