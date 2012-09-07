import socket
def decodeRecv(sock, num = 8):
	data = sock.recv(num)
	data = list(data)
	i = num - 2
	while i >= 0:
		data[i] = chr(ord(data[i]) ^ ord(data[i + 1]))
		i -= 1
	return ''.join(data)
def encodeSend(sock, data, num = 8):
	data = list(data)
	l = len(data)
	for i in xrange(l, num):
		for j in xrange(i, i + num):
			if j == l - 1:
				pass
			elif j >= l:
<<<<<<< HEAD
				data.append(0)
=======
				data.append(chr(0))
>>>>>>> origin/master
			else:
				data[j] = chr(ord(data[j]) ^ ord(data[j + 1]))
	return sock.send(''.join(data))
