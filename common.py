import socket
def decodeRecv(sock, num = 8):
	data = sock.recv(num);
	i = num - 2
	while i >= 0:
		data[i] = data[i] ^ data[i + 1]