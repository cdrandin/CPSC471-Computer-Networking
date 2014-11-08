
import socket
import os
import sys

def main():
	server_name = sys.argv[1]
	port        = (int)(sys.argv[2])

	print '1'
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print '2'
	clientSocket.connect((server_name, port))
	print '3'

	data = "Hello world! This is a very long string."

	bytesSent = 0

	print '4'
	while bytesSent is not len(data):
		bytesSent += clientSocket.send(data[bytesSent:])
	print '5'

	clientSocket.close()

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "USAGE: python %s <server_machine> <server_port>" %(sys.argv[0])
		exit()

	main()