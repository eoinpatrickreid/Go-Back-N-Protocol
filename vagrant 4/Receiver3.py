# Eoin Reid s1858933
from socket import *
import sys

BUFF_SZ = 1027


def main(port, file_name):
    # Open a socket and bind it
    rs = socket(AF_INET, SOCK_DGRAM)
    rs.bind(('localhost', port))
    # Open file to write to
    f = open(file_name, "wb")
    # Set expected Sequence number to be 1
    expected = 1
    last_received = 0
    while True:
        # Receive packet from scoket and break it down into sequence number, EOF flag and payload (data)
        pkt, address = rs.recvfrom(BUFF_SZ)
        seq = int.from_bytes(pkt[:2], byteorder='big')
        eof = pkt[2]
        data = pkt[3:]
        # If we didn't receive the expected packet
        if seq != expected:
            # Send NAK, which is the ACK of the last correctly received packet (as described in textbook)
            rs.sendto(last_received.to_bytes(2, byteorder='big'), address)
            continue
        else:
            # If the packet is the one we want then set last_received current packet
            last_received = seq
            # If not the last packet write the data to the file, send ACK to socket and continue loop
            if eof != 1:
                f.write(data)
                rs.sendto(expected.to_bytes(2, byteorder='big'), address)
            # If it is the last packet, write the data then send 10 ACKS to socket to ensure Sender receives final ACK
            # ... and break loop
            elif eof == 1:
                f.write(data)
                for x in range(0, 9):
                    rs.sendto(expected.to_bytes(2, byteorder='big'), address)
                expected += 1
                break
        expected += 1
    # Close socket and file
    f.close()
    rs.close()


if __name__ == '__main__':
    # Take command line arguments and pass them into main()
    p = int(sys.argv[1])
    fileN = sys.argv[2]
    main(p, fileN)
