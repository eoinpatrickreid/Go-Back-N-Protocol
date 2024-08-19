# Eoin Reid s1858933
from socket import *
import sys
from time import perf_counter

BUFF_SZ = 1024
HEADER_SZ = 3


# Function takes sequence number, end of file flag...
# and data and attaches the head (sequence number and eof) in byte form to the data
def form_pkt(seq, eof, data):
    head = bytes([seq >> 8, seq % 256, eof])
    return head + data


def main(h, p, f, rt):
    host_name = h
    port = p

    # Open our file and read the data from it into an array of bytes
    file = open(f, 'rb')
    data = bytearray(file.read())
    data_left = len(data)
    # Set our retry timeout value, divide by 1000 to get milliseconds
    retry_timeout = int(rt)/1000
    s = socket(AF_INET, SOCK_DGRAM)
    eof = 0
    retransmissions = 0
    seq_no = 0
    # Take note of the start time to calculate throughput later
    start = perf_counter()

    # While we still have data to send:
    while data_left > 0:
        receivedAck = False
        correct = False
        ackSeq = 0
        # If there is more than one packet left to send
        if data_left > 1024:
            # Form a packet with the data corresponding to current sequence number and send it through the socket
            packet = form_pkt(seq_no, eof, data[seq_no*BUFF_SZ:seq_no*BUFF_SZ+BUFF_SZ])
            s.sendto(packet, (host_name, port))
            # Until packet is correctly acked
            while not correct:
                # Start a timer and wait to receive the ack from the receiver file, if we receive the ack
                # read off the data set receivedAck to true
                try:
                    s.settimeout(retry_timeout)
                    ack, sender = s.recvfrom(2)
                    ackSeq = int.from_bytes(ack[:2], 'big')
                    receivedAck = True
                # If the timer goes off before we receive an ack set receivedAck to False
                except timeout:
                    receivedAck = False
                # If we received an ack and it is the correct ack then set correct to true, breaking the while loop
                if seq_no == ackSeq and receivedAck == True:
                    correct = True
                # Otherwise retransmit the packet
                else:
                    s.sendto(packet, (host_name, port))
                    retransmissions += 1
            seq_no += 1
            data_left -= 1024
        # If we have one more packet left to send
        else:
            # Set out EOF flag to 1
            eof = 1
            # Go through the same process as above, sending the packet then waiting to receive an ack and...
            # Retransmitting if the ack isn't received in time
            receivedAck = False
            correct = False
            ackSeq = 0
            packet = form_pkt(seq_no, eof, data[seq_no * BUFF_SZ:])
            s.sendto(packet, (host_name, port))
            while not correct:
                try:
                    s.settimeout(retry_timeout/1000)
                    ack, sender = s.recvfrom(2)
                    ackSeq = int.from_bytes(ack[:2], 'big')
                    receivedAck = True
                except timeout:
                    receivedAck = False
                if seq_no == ackSeq and receivedAck:
                    correct = True
                else:
                    s.sendto(packet, (host_name, port))
                    retransmissions += 1
            seq_no += 1
            data_left -= 1024
    # Calculate the transfer time to be the current time minus the start time, the size of the file in kilobytes...
    # and then the throughput to be the file size divided by the transfer time
    transfer_time = perf_counter() - start
    file_size = len(data)/1000
    throughput = round(file_size/transfer_time)
    print(str(retransmissions) + " " + str(throughput))


if __name__ == "__main__":
    # Read in command line arguments and pass them onto main function
    host = sys.argv[1]
    p = int(sys.argv[2])
    fileA = sys.argv[3]
    time = sys.argv[4]
    main(host, p, fileA, time)
