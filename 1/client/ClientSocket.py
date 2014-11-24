import socket
import cPickle as pickle

class ClientSocket:
    def __init__(self, host, ip, socket):
        self.host      = host
        self.ip        = ip
        self.socket    = socket
        self.connected = False

    # Connects to server. If already connected it won't run.
    # Returns true if connection established; otherwise false.
    def connect(self):
        if not self.connected:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.socket.connect((self.host,self.ip))
                self.connected = True
            except socket.error:
                self.connected = False

        return self.connected

    # Close connection
    def close(self):
        self.socket.close()
        self.connected = False

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