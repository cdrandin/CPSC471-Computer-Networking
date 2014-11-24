import threading
import socket
import commands
import os
import cPickle as pickle

COMMANDS = (lambda **enums: type('Enum', (), enums))(UNDEFINED = 0, QUIT = 1, PUT = 2, GET = 3, LS = 4)

class ClientThread(threading.Thread):
    def __init__(self, socket, ip, port):
        threading.Thread.__init__(self)     
        self.socket       = socket
        self.ip           = ip
        self.port         = port

    def run(self):
        print 'Accepted connection from client: ', (self.ip, self.port)

        continue_session = True
        while continue_session:
            info = self.recv()
            print 'Got: ', info, ' from ', (self.ip, self.port)

            # Quit
            if info['command'] is COMMANDS.QUIT:
                print 'Quiting with ', (self.ip, self.port)
                self.socket.close()
                continue_session = False

            # Handle client's commands
            else:
                data_info = {}

                if info['command'] is COMMANDS.LS:
                    data_info['data'] = [line for line in commands.getstatusoutput('ls -l')]
                    data_info['status'] = 'success'
                    self.send(data_info)
                elif info['command'] is COMMANDS.PUT:
                    data_info['status'] = 'success'

                    # Let client know we are ready
                    self.send(data_info)

                    # Unpack file
                    data_info = self.recv()

                    # If everything went well...
                    if data_info['status'] in 'success':
                        changes = ''
                        # copied file, add .copy extendtion before file extension
                        if os.path.isfile(info['file_name']):
                            info['file_name'] = info['file_name'][:info['file_name'].rfind('.')]+'.copy'+info['file_name'][info['file_name'].rfind('.'):]
                            changes = 'File name taken. Changing file: %s ==> %s' %(info['file_name'], info['file_name'])

                        # write file
                        with open(info['file_name'], 'w') as outfile:
                            outfile.write(data_info['data'])

                        # let client know all was good and changes if any
                        data_info = {'status': 'success', 'changes': changes}
                        self.send(data_info)

                    # Ignore, errors happened
                    else:
                        pass

                elif info['command'] is COMMANDS.GET:
                    # file exist on server
                    if os.path.isfile(info['file_name']):
                        data_info['status'] = 'success'

                        # read file to send to client
                        with open(info['file_name'], 'r') as infile:
                            data_info['data'] = infile.read()
                            data_info['file_length'] = len(data_info['data'])
                            
                        self.send(data_info)

                    # let client know they aren't getting a file
                    else:
                        data_info['status'] = 'File does not exist.'
                        self.send(data_info)

    def send(self, data):
        # Pickle object
        info = pickle.dumps(data, -1) 
        dataSizeStr = str(len(info))

        # Append length of the data as header in front
        while len(dataSizeStr) < 10:
            dataSizeStr = '0' + dataSizeStr

        # Add length in front
        info = dataSizeStr + info

        # Keep sending
        bytesSent = 0
        while len(info) > bytesSent:
            bytesSent += self.socket.send(info[bytesSent:])

    # Get what was sent correctly. Returning what ever pickled object was sent over the network
    def recv(self):
        # The temporary buffer to store the received
        # data.
        recvBuff = ''

        # The size of the incoming file
        data_size = 0    

        # The buffer containing the file size
        data_sizeBuff = ''

        # Receive the first 10 bytes indicating the size of the message
        data_sizeBuff = self._recvAll(10)
            
        # Get the file size
        data_size = int(data_sizeBuff)

        # Get remaining data
        info = self._recvAll(data_size)

        # unpickle object from returned pickled object
        info = pickle.loads(info)

        return info

    # Get the buffered data given a specific number of bytes
    def _recvAll(self, numBytes):
        # The buffer
        recvBuff = ''
        
        # The temporary buffer
        tmpBuff = ''
        
        # Keep receiving till all is received
        while len(recvBuff) < numBytes:
            # Attempt to receive bytes
            tmpBuff =  self.socket.recv(numBytes)
            
            # The other side has closed the socket
            if not tmpBuff:
                break
            # Add the received bytes to the buffer
           
            recvBuff += tmpBuff
        return recvBuff