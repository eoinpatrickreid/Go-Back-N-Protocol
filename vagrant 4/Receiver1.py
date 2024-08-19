# Eoin Reid s1858933
from socket import *
import sys


def ReceiveFile(p, fileN):
    port = p
    fileName = fileN
    serverName = 'localhost'
    # Open a socket and the file we are going to write to
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind((serverName, port))
    f = open(fileName, "wb")
    while True:
        # Receive the packet and break it down into it's components
        packet, address = s.recvfrom(1027)
        sn1, sn2, eof = list(packet[:3])
        seq_num = int.from_bytes(packet[0:2], 'big')
        data = packet[3:]
        # print(seq_num)
        # If the EOF flag = 1 break the loop
        if eof:
            break
        # Otherwise write the payload to our file
        f.write(data)
    f.close()
    s.close()


if __name__ == '__main__':
    # Read in arguments from command line and call ReceiveFile function
    p = int(sys.argv[1])
    fileN = sys.argv[2]
    ReceiveFile(p, fileN)


