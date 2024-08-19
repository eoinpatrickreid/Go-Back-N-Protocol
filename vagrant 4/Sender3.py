# Eoin Reid s1858933
from socket import *
import sys
from time import perf_counter
import math

BUFF_SZ = 1024
HEADER_SZ = 3


# Function takes, sequence number, EOF flag and data and forms a packet
def form_pkt(seq, eof, data):
    head = bytes([seq >> 8, seq % 256, eof])
    return head + data


def main(host_name, port, file_name, delay, window_size):
    # Open a socket and make it non-blocking
    s = socket(AF_INET, SOCK_DGRAM)
    s.setblocking(False)
    # Open the file and read the data into a byte array, plus calculate the number of segments we need to send
    file = open(file_name, 'rb')
    data = bytearray(file.read())
    segments = math.ceil(len(data) / BUFF_SZ)
    # Variables to keep track of the packets were operating on
    base = 1
    sequence_no = 1
    packet_number = 0
    start = perf_counter()
    # While not at the last segment:
    while sequence_no != segments:
        try:
            # List to keep track of the packets we will need to resend in the case of lost packets
            resend = []
            # While current packet is within send window and isn't the final packet
            while (sequence_no < base + window_size) and (sequence_no != segments):
                # Form the packet with the relevant sequence number EOF flag and data
                packet = form_pkt(sequence_no, 0, data[packet_number * 1024:packet_number * 1024 + 1024])
                # Add the packet to the resend list
                resend.append(packet)
                # Send the packet
                s.sendto(packet, (host_name, port))
                # If the packet we sent is our base packet then we start a timer
                if base == sequence_no:
                    s.settimeout(delay)
                sequence_no += 1
                packet_number += 1
            correct = False
            # While we haven't received the correct ACK
            while not correct:
                try:
                    # Receive packet from socket and withdraw the sequence number from it
                    base, address = s.recvfrom(2)
                    base = int.from_bytes(base, 'big') + 1
                    received = True
                    # If base is equal to sequence number, we have received all packets that we were expecting
                    if (base == sequence_no) and received:
                        # In which case we stop our timer and set correct to true to to break the while loop
                        s.settimeout(0)
                        correct = True
                        break
                # In the case of a timeout we resend all of the packets in our resend window
                except timeout:
                    for pkt in resend:
                        s.sendto(pkt, (host_name, port))
                    continue
        except:
            continue

    # If we have reached the last segment
    if sequence_no == segments:
        # Form final packet with EOF flag = 1 and send it
        packet = form_pkt(sequence_no, 1, data[packet_number * 1024:packet_number * 1024 + 1024])
        s.sendto(packet, (host_name, port))
        # Start a timer for the final packet
        s.settimeout(delay)
        sequence_no += 1
        packet_number += 1

        correct = False
        # Until correct Ack received:
        while not correct:
            try:
                # Receive ACK and break down into components
                base, address = s.recvfrom(2)
                base = int.from_bytes(base, 'big') + 1
                received = True
                # If correct ACK received; stop timer and break loop
                if (base == sequence_no) and received:
                    s.settimeout(0)
                    correct = True
            # If the timer goes off then resend the final packet and wait for ACK again
            except timeout:
                s.sendto(packet, (host_name, port))
                continue

    file.close()
    s.close()
    # Calculate the transfer time to be current time - start time
    transfer_time = perf_counter() - start
    file_size = len(data) / 1000
    # Calculate and output the throughput
    throughput = round(file_size / transfer_time)
    print(throughput)


if __name__ == "__main__":
    # Read in command line arguments and pass them onto main function
    host = sys.argv[1]
    p = int(sys.argv[2])
    fileA = sys.argv[3]
    time = int(sys.argv[4]) / 1000
    window = int(sys.argv[5])
    main(host, p, fileA, time, window)
