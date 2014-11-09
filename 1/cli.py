
import socket
import os
import sys
import cPickle as pickle

def enum(**enums):
    return type('Enum', (), enums)

COMMANDS = enum(UNDEFINED = 0, QUIT = 1, PUT = 2, GET = 3, LS = 4)

def clearScreen():
	os.system('clear')

# Process what type of command the user wanted
def handleInput():
	success = False
	command = COMMANDS.UNDEFINED
	response = None

	while not success:
		try:
			response = raw_input('ftp> ')
			response = response.split()

			if checkQuitHandle(response):
				success = True
				command = COMMANDS.QUIT
			elif checkGetHandle(response):
				success = True
				command = COMMANDS.GET
				handleGet(response[1])
			elif checkPutHandle(response):
				success = True
				command = COMMANDS.PUT
				handlePut(response[1])
			elif checkLsHandle(response):
				success = True
				command = COMMANDS.LS
				handleLs()
			else:
				print('Invalid command: %s'%(response[0]))
				success = False

		except KeyboardInterrupt:
			command = COMMANDS.QUIT

	return command, response

def checkGetHandle(response):
	return len(response) is 2 and 'get' in response[0].lower()

def handleGet(file_name):
	print 'get <%s>' %(file_name)

def checkPutHandle(response):
	return len(response) is 2 and 'put' in response[0].lower()

def handlePut(file_name):
	print 'put <%s>' %(file_name)

def checkLsHandle(response):
	return len(response) is 1 and 'ls' in response[0].lower()

def handleLs():
	print 'ls'

def checkQuitHandle(response):
	return len(response) is 1 and 'quit' in response[0].lower()

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

def main():
	clearScreen()

	serverName = sys.argv[1]
	serverPort = (int)(sys.argv[2])

	# will be the control socket to send over commands
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	clientSocket.connect((serverName,serverPort))

	while 1:
		command, response = handleInput()

		if command is not COMMANDS.UNDEFINED:
			# organize commands to get sent to server
			info = {'command': command, 'file_name': response[1] if len(response) is 2 else ""}

			sendInfo(clientSocket, info)

			# Time to kill the control connection. Tell serve to close connection and we close too
			if command is COMMANDS.QUIT:
				clientSocket.close()
				print "Closing connection... Quiting..."
				exit()

			# We got more stuff incoming from the server to handle the commands we requested
			# Open up new connection for the data channel
			else:
				if command is COMMANDS.LS:
					info = unpackInfo(clientSocket)
					for i in info:
						print i



if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'USAGE: python %s <server_machine> <server_port>' %(sys.argv[0])
		exit()

	main()
