
import socket
import os
import sys
from ClientSocket import ClientSocket

COMMANDS = (lambda **enums: type('Enum', (), enums))(UNDEFINED = 0, QUIT = 1, PUT = 2, GET = 3, LS = 4)

client = None

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
                # Accept allows blank responses
                try:
                    print('Invalid command: %s'%(response[0]))
                except IndexError:
                    pass
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


def main():
    clearScreen()

    # will be the control socket to send over commands
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client = ClientSocket(sys.argv[1], (int)(sys.argv[2]), clientSocket)
    connected = client.connect()

    while client.connected:
        command, response = handleInput()

        if command is not COMMANDS.UNDEFINED:
            # organize commands to get sent to server
            info = {'command': command, 'file_name': response[1] if len(response) is 2 else ""}

            client.send(info)

            # Time to kill the control connection. Tell serve to close connection and we close too
            if command is COMMANDS.QUIT:
                client.close()
                print "Closing connection... Quiting..."
                exit()

            # We got more stuff incoming from the server to handle the commands we requested
            # Open up new connection for the data channel
            else:
                # server replied to the client's command request
                data_info = client.recv()

                if command is COMMANDS.LS:
                    for i in data_info['data']:
                        print i

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

                            client.send(data_info)

                            # Did it successfully send
                            data_info = client.recv()

                            if data_info['status'] in 'success':
                                # any changes?
                                if data_info['changes'] not in '':
                                    print 'Server modified file: %s' % (data_info['changes'])

                        # File doesn't exist
                        else:
                            # Let server know to ignore file transfer
                            data_info = {'status': 'No file'}
                            client.send(data_info)

                            print "File does not exist"
                    else:
                        print "Server is busy"

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