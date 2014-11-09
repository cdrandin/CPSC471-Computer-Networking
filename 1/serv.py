
import socket
import os
import sys
import cPickle as pickle
import commands

def enum(**enums):
    return type('Enum', (), enums)

COMMANDS = enum(UNDEFINED = 0, QUIT = 1, PUT = 2, GET = 3, LS = 4)

# Get what was sent correctly. Returning what ever pickled object was sent over the network
def unpackInfo(clientSocket):
	# The temporary buffer to store the received
	# data.
	recvBuff = ''

	# The size of the incoming file
	fileSize = 0	

	# The buffer containing the file size
	fileSizeBuff = ''

	# Receive the first 10 bytes indicating the
	# size of the file
	fileSizeBuff = recvAll(clientSocket, 10)
		
	# Get the file size
	fileSize = int(fileSizeBuff)

	#print 'The file size is ', fileSize

	# Get the file data
	info = recvAll(clientSocket, fileSize)

	# unpickle object from returned pickled object
	info = pickle.loads(info)

	return info
	
# Get the buffered data given a specific number of bytes
def recvAll(sock, numBytes):

	# The buffer
	recvBuff = ''
	
	# The temporary buffer
	tmpBuff = ''
	
	# Keep receiving till all is received
	while len(recvBuff) < numBytes:
		
		# Attempt to receive bytes
		tmpBuff =  sock.recv(numBytes)
		
		# The other side has closed the socket
		if not tmpBuff:
			break
		
		# Add the received bytes to the buffer
		recvBuff += tmpBuff
	
	return recvBuff

# Pickle object. Include header length and send off to socket
def sendInfo(clientSocket, info):
	# Pickle object
	info = pickle.dumps(info, -1) 

	dataSizeStr = str(len(info))

	# Append length of the data as header in front
	while len(dataSizeStr) < 10:
		dataSizeStr = '0' + dataSizeStr

	info = dataSizeStr + info

	# Keep sending
	bytesSent = 0
	while len(info) > bytesSent:
		bytesSent += clientSocket.send(info[bytesSent:])


def lsOutput():
	return [line for line in commands.getstatusoutput('ls -l')]

def main():
	port = (int)(sys.argv[1])
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serverSocket.bind(('localhost', port))
	serverSocket.listen(1)

	print('Server ready')
	while 1:
		clientSocket , addr = serverSocket.accept()

		print 'Accepted connection from client: ', addr

		cont = True
		while cont:
			info = unpackInfo(clientSocket)

			print 'The file data is: '
			print info

			# Quit
			if info['command'] is COMMANDS.QUIT:
				print 'Quiting with ', addr
				clientSocket.close()
				cont = False

			# Didn't quit so respond to client with info
			else:
				if info['command'] is COMMANDS.LS:
					sendInfo(clientSocket, lsOutput())

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'USAGE: python %s <port_number>' %(sys.agv[0])
		exit()

	try:
		main()
	except KeyboardInterrupt:
		print "\nKeyboardInterrupt: Quiting silently"