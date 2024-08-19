# Eoin Reid S1858933
from socket import *
import sys

BUFF_SZ = 1024
HEADER_SZ = 3


def main(p, file_n):
    port = p
    fileName = file_n
    serverName = 'localhost'
    # Open a socket and a file
    sr = socket(AF_INET, SOCK_DGRAM)
    sr.bind((serverName, port))
    f = open(fileName, "wb")
    # Variables to keep track of the packets received
    received = 0
    last_seq = -1
    final_pkt = False

    # While theres still packets to receive:
    while not final_pkt:
        # Receive packet and break it down into it's components
        packet, address = sr.recvfrom(1027)
        curr_seq = int.from_bytes(packet[:2], byteorder='big')
        eof = packet[2]
        data = packet[3:]
        # If the received packet is the subsequent packet to the last one received:
        if curr_seq == last_seq+1:
            # Accept the packet and write it's data to the file
            last_seq = curr_seq
            f.write(data)
            # Create and send an acknowledgement packet to the sender file
            ack = curr_seq.to_bytes(2, byteorder='big')
            sr.sendto(ack, address)
            received += 1
        # Otherwise create and send a NAK packet
        else:
            nak = last_seq.to_bytes(2, byteorder='big')
            sr.sendto(nak, address)
        # If the packet contains the EOF flag then set final packet to be true, breaking the while loop
        if eof == 1:
            final_pkt = True
            for x in range(0, 9):
                sr.sendto(ack, address)
    # Close the file and the socket
    f.close()
    sr.close()


if __name__ == '__main__':
    # Read in command line arguments
    port = int(sys.argv[1])
    fileN = sys.argv[2]
    main(port, fileN)
