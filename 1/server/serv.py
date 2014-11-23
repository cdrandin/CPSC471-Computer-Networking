
import socket
import os
import sys
import cPickle as pickle
import commands

COMMANDS = (lambda **enums: type('Enum', (), enums))(UNDEFINED = 0, QUIT = 1, PUT = 2, GET = 3, LS = 4)

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


def lsOutput():
    return [line for line in commands.getstatusoutput('ls -l')]

def main():
    server_name = 'localhost'#'ecs.fullerton.edu'
    port = (int)(sys.argv[1])
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((server_name, port))
    serverSocket.listen(1)

    print('Server ready')
    while 1:
        clientSocket , addr = serverSocket.accept()

        print 'Accepted connection from client: ', addr

        continue_session = True
        while continue_session:
            info = unpackInfo(clientSocket)

            print 'The file data is: '
            print info

            # Quit
            if info['command'] is COMMANDS.QUIT:
                print 'Quiting with ', addr
                clientSocket.close()
                continue_session = False

            # Didn't quit so respond to client with info
            else:
                portnumber = clientSocket.recv(1024).decode()
                new_port       = int(portnumber)
                print 'port', new_port

                dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dataSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                dataSocket.connect((addr[0], new_port))

                data_info = {}

                # LS 
                if info['command'] is COMMANDS.LS:
                    data_info['data'] = lsOutput()
                    data_info['status'] = 'success'
                    sendInfo(clientSocket, data_info)
                    # HELP
                    # When I disable this and the one on the client side to try to send data a socket.error is raised
                    #dataSocket.send('hello world'.encode())

                # Send file data over to client
                elif info['command'] is COMMANDS.GET:
                    # file exist on server
                    if os.path.isfile(info['file_name']):
                        data_info['status'] = 'success'

                        # read file to send to client
                        with open(info['file_name'], 'r') as infile:
                            data_info['data'] = infile.read()
                            data_info['file_length'] = len(data_info['data'])
                            
                        sendInfo(clientSocket, data_info)

                    # let client know they aren't getting a file
                    else:
                        data_info['status'] = 'File does not exist.'
                        sendInfo(clientSocket, data_info)

                # Get data from client
                elif info['command'] is COMMANDS.PUT:
                    data_info['status'] = 'success'

                    # Let client know we are ready
                    sendInfo(clientSocket, data_info)

                    # Unpack file
                    data_info = unpackInfo(clientSocket)

                    # If everything went well...
                    if data_info['status'] in 'success':
                        changes = ''

                        # copied file, add .copy extendtion before file extension
                        if os.path.isfile(info['file_name']):
                            new_file_name = info['file_name'][:info['file_name'].rfind('.')]+'.copy'+info['file_name'][info['file_name'].rfind('.'):]
                            changes = 'File name taken. Changing file: %s ==> %s' %(info['file_name'], new_file_name)

                        # write file
                        with open(new_file_name, 'w') as outfile:
                            outfile.write(data_info['data'])

                        # let client know all was good and changes if any
                        data_info = {'status': 'success', 'changes': changes}
                        sendInfo(clientSocket, data_info)

                    # Ignore, errors happened
                    else:
                        pass

                dataSocket.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'USAGE: python %s <port_number>' %(sys.agv[0])
        exit()

    try:
        main()
    except KeyboardInterrupt:
        print "\nKeyboardInterrupt: Quiting silently"