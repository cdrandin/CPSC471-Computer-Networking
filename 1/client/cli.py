
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

            elif checkPutHandle(response):
                success = True
                command = COMMANDS.PUT

            elif checkLsHandle(response):
                success = True
                command = COMMANDS.LS
            else:
                print('Invalid command: %s'%(response[0]))
                success = False

        except KeyboardInterrupt:
            command = COMMANDS.QUIT

    return command, response

def checkGetHandle(response):
    return len(response) is 2 and 'get' in response[0].lower()

def checkPutHandle(response):
    return len(response) is 2 and 'put' in response[0].lower()

def checkLsHandle(response):
    return len(response) is 1 and 'ls' in response[0].lower()

def checkQuitHandle(response):
    return len(response) is 1 and 'quit' in response[0].lower()

# Pickle object. Include header length and send off to socket
def sendInfo(socket, info):
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
        bytesSent += socket.send(info[bytesSent:])

# Get what was sent correctly. Returning what ever pickled object was sent over the network
def unpackInfo(clientSocket):
    # The temporary buffer to store the received
    # data.
    recvBuff = ''

    # The size of the incoming file
    data_size = 0    

    # The buffer containing the file size
    data_sizeBuff = ''

    # Receive the first 10 bytes indicating the
    # size of the file
    data_sizeBuff = recvAll(clientSocket, 10)
        
    # Get the file size
    data_size = int(data_sizeBuff)

    #print 'The file size is ', data_size

    # Get the file data
    info = recvAll(clientSocket, data_size)

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
                # create data channel
                dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dataSocket.bind(('',0))
                portnumber = dataSocket.getsockname()[1]

                dataSocket.listen(1)
                clientSocket.send(str(portnumber).encode())

                clientDataSock, tempaddr = dataSocket.accept()

                print 'Connected with ', tempaddr, 'for data transfer'

                # Get new info from server using data channel
                data_info = unpackInfo(clientSocket)
                # HELP
                # When I disable this and the one on the server side to try to send data a socket.error is raised
                #print dataSocket.recv(1024).decode()

                dataSocket.close()

                # Translate the command
                if data_info['status'] in 'success':
                    if command is COMMANDS.LS:
                        for i in data_info['data']:
                            print i

                    # Get file data to server
                    elif command is COMMANDS.PUT:
                        # Server ready for file transfer
                        if data_info['status'] in 'success':

                            # Before we send lets make sure the file exis
                            if os.path.isfile(info['file_name']):
                                # Read file to send to server
                                with open(info['file_name'], 'r') as infile:
                                    data_info['status'] = 'success'
                                    data_info['data'] = infile.read()
                                    data_info['file_length'] = len(data_info['data'])

                                sendInfo(clientSocket, data_info)

                                # Did ti successfully send
                                data_info = unpackInfo(clientSocket)

                                if data_info['status'] in 'success':
                                    # any changes?
                                    if data_info['changes'] != '':
                                        print 'Server modified file: %s' % (data_info['changes'])

                            # File doesn't exist
                            else:
                                # Let server know to ignore file transfer
                                data_info = {'status': 'No file'}
                                sendInfo(clientSocket, data_info)

                                print "File does not exist"
                        else:
                            print "Server is busy"

                    # Get file data from server
                    elif command is COMMANDS.GET:
                        if data_info['status'] in 'success':
                            with open(info['file_name'], 'w') as outfile:
                                outfile.write(data_info['data'])
                                
                            print 'Success delivery'
                            print '%s  ~%i bytes' %(info['file_name'], data_info['file_length'])
                else:
                    print 'Error: ', data_info['status']

        else:
            print "Unknown command"


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'USAGE: python %s <server_machine> <server_port>' %(sys.argv[0])
        exit()

    main()
