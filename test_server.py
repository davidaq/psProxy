import socket
from time import sleep
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 7777))
server.listen(5)
socket.setdefaulttimeout(2)

while 1:
	(client, addr) = server.accept()
	print "incomming connection"
	client.send("server is running")
	client.send("second message")
	client.recv(128)
	client.close()
'''
	sleep(10)
	print "Counte down over"
	print client.send("Another message")
'''
