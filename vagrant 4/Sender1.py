# Eoin Reid s1858933
import sys
from socket import *
import time


def SendFile(host, p, fileA):
    remoteHost = host
    port = int(p)
    fileName = fileA

    # open a socket connection
    s = socket(AF_INET, SOCK_DGRAM)
    sequenceNo = 0
    try:
        # open the file in binary format
        f = open(fileName, "rb")
        while True:
            eof = 0
            buff = f.read(1024)
            # If buff is empty, we've reached the EOF and create an empty packet with EOF flag = 1
            if not buff:
                eof = 1
                data = bytes([sequenceNo >> 8, sequenceNo % 256, eof])
                data = data + b""
            # Otherwise there is still data to send and we create a packet with this data to send
            else:
                data = bytes([sequenceNo >> 8, sequenceNo % 256, eof])
                data = data + buff
            # Send whichever packet has been created through the socket
            # print(sequenceNo)
            s.sendto(data, (remoteHost, port))
            # If EOF flag = 1 file has been sent and we break out of the loop
            if eof == 1:
                break
            sequenceNo += 1
            time.sleep(0.001)
        f.close()
        # Catch the error if the filename is wrong/file doesn't exist
    except OSError as e:
        print("Couldn't find file")
    s.close()


if __name__ == '__main__':
    # read in the command line arguments
    host = sys.argv[1]
    p = int(sys.argv[2])
    fileA = sys.argv[3]

    # call the sendFile function
    SendFile(host, p, fileA)
