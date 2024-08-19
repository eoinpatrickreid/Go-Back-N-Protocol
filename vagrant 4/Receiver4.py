# Eoin Reid s1858933
import sys
import math
import time
from socket import *
import os
import struct

BUFF_SZ = 1027


def main(port, file_name, window_size):
    # Open socket and bind it to localhost and port
    rs = socket(AF_INET, SOCK_DGRAM)
    rs.bind(('localhost', port))
    f = open(file_name, "wb")
    # set variables to keep track of data and packets
    base = 1
    buffer = {}
    prev_received = []
    done = False
    # Until all packets have been acked:
    while not done:
        # receive the packet from the socket and extract the sequence number, eof flag and payload from it
        pkt, addr = rs.recvfrom(BUFF_SZ)
        seq = int.from_bytes(pkt[:2], byteorder='big')
        eof = pkt[2]
        data = pkt[3:]
        # If the sequence number is in the previous window then simply acknowledge it and continue loop
        if base - window_size <= seq <= base - 1:
            rs.sendto(seq.to_bytes(2, byteorder='big'), addr)
            continue
        # If the packet is in the receiver window then:
        if seq in range(base, base+window_size):
            # If packet not previously acked then add its data to the data buffer
            if seq not in prev_received:
                buffer[seq] = data
            # Send the acknowledgement
            rs.sendto(seq.to_bytes(2, byteorder='big'), addr)
            # If packet received is the base packet:
            if seq == base:
                # write its data to the file
                f.write(data)
                written = 1
                finished = False
                next_seq = seq+1
                # Write each packet that is in the buffer and is consecutive to the base packet; that is,
                # ...each subsequently numbered packet following from the base packet
                while not finished:
                    if next_seq in buffer:
                        f.write(buffer[next_seq])
                        next_seq += 1
                        written += 1
                    else:
                        finished = True
                base += written
        if eof == 1:
            for x in range(0, 9):
                rs.sendto(seq.to_bytes(2, byteorder='big'), addr)
            done = True

    f.close()
    rs.close()


if __name__ == '__main__':
    p = int(sys.argv[1])
    fileN = sys.argv[2]
    window = int(sys.argv[3])
    main(p, fileN, window)

