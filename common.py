import socket
def decodeRecv(sock, num = 8):
	data = sock.recv(num)
	i = num - 2
	while i >= 0:
		data[i] = data[i] ^ data[i + 1]
	return data
def encodeSend(sock, data, num = 8):
	for i in xrange(len(data), num):
		for j in xrange(num):
			if j == l - 1:
				pass
			elif j > l:
				data[j] = 0
			else:
				data[j] = data[j] ^ data[j + 1];
	return sock.send(data)
			