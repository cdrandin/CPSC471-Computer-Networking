import socket
import os
import sys
from ClientThread import ClientThread

ftpLimit = 10

def clearScreen():
    os.system('clear')

def main():
    clearScreen()
    port = (int)(sys.argv[1])

    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listenSocket.bind(('', port))
    listenSocket.listen(ftpLimit)

    threads   = []
    threadSeq = 0

    print('Server ready')
    while 1:
        client, address = listenSocket.accept()

        threadSeq += 1
        newthread = ClientThread(client, address[0], address[1])
        newthread.start()
        threads.append(newthread)

    # wait for threads
    for t in threads:
        t.join()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'USAGE: python %s <port_number>' %(sys.argv[0])
        exit()

    try:
        main()
    except KeyboardInterrupt:
        print "\nKeyboardInterrupt: Quiting silently"
