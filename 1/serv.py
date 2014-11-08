
import socket
import os
import sys

def main():
	port = (int)(sys.argv[1])
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind(('', port))
	serverSocket.listen(1)

	print("Server ready")
	while 1:
		connectionSocket , addr = serverSocket.accept()

		tmpBuff = ""

		while len(data) is not 40:
			tmpBuff = connectionSocket.recv(40)

			if not tmpBuff:
				break

			data += tmpBuff

		print data
		connectionSocket.close()


if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "USAGE: python %s <port_number>" %(sys.agv[0])
		exit()

	main()