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
def hostalive(sockinfo):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.settimeout(4)  # 6 second
		sock.connect(sockinfo)
		print "Remote: ", sockinfo, " is Alive"
		sock.close()
		return True
	except Exception:
		print "Remote: ", sockinfo, " is Dead"
		sock.close()
		return False