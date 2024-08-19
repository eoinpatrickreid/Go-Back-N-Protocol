# Eoin Reid s1858933
import struct
import sys
from time import perf_counter
from socket import *
from threading import Thread, Lock
import math

BUFF_SZ = 1024
HEADER_SZ = 3

# Function takes, sequence number, EOF flag and data and forms a packet
def form_pkt(seq, eof, data):
    head = bytes([seq >> 8, seq % 256, eof])
    return head + data

# Take command line arguments and create variables for them
host = sys.argv[1]
port = int(sys.argv[2])
file_name = sys.argv[3]
timeout = int(sys.argv[4]) / 1000
window = int(sys.argv[5])
# Open the file and read data into byte array, plus get the number of packets we will have to send
file = open(file_name, 'rb')
data = bytearray(file.read())
file.close()
segments = math.ceil(len(data) / BUFF_SZ)
# Open a socket to send packets to
s = socket(AF_INET, SOCK_DGRAM)
# Instantiate variables to help us keep track of base, window, and packets
base = 1
seq_No = 1
prevNotQueued = 0
prevWindowCount = 0
pkt_No = 0
eof = 0
lastWindowRetransmissions = 10
isTimer = True
lastWindowAck = False
finished = False
acknowledged = set()
lock = Lock()
fullPackets = [None] * (segments + 1)

# Note the time that we start the transfer
start = perf_counter()

# Send function in order to send packets, takes boolean last_pkt set to true if it's last packet and false otherwise
def send(last_pkt):
    # Global declarations for global variables the function uses
    global base
    global lock
    global pkt_No
    global seq_No
    global clock
    global isTimer
    global eof

    # Acquire the lock allowing thread to change variables without causing errors
    with lock:
        # If the sequence number is within the window then we proceed to send the packet
        if seq_No < base + window:
            # If it's the last packet we set the EOF flag to 1
            if last_pkt:
                eof = 1
            # Form the relevant packet and store it in fullPackets array indexed at current sequence number
            # ...This is so that we can easily retransmit packets when we need to
            fullPackets[seq_No] = form_pkt(seq_No, eof, data[pkt_No * 1024:pkt_No * 1024 + 1024])
            # Send the packet into the socket
            s.sendto(fullPackets[seq_No], (host, port))
            # If the packet is the base packet then we set the timer
            if seq_No == base:
                isTimer = True
                clock = perf_counter()
            seq_No += 1
            pkt_No += 1
            # Return true to signify we have sent the packet
            return True
        else:
            # Return false to signify we failed to send the packet
            return False


# Receive thread, receives and processes acknowledgements
def receive():
    # Instantiate the global variables we use
    global base
    global acknowledged
    global isTimer
    global lock
    global lastWindowAck
    global clock
    global finished


    while not finished:
        # Receive packet from the socket and extract ack sequence number from it
        data, addr = s.recvfrom(2)
        ackNum = int.from_bytes(data[:2], 'big')
        with lock:
            # Note that the packet has been acked
            acknowledged.add(ackNum)
            # If we're in the final window set lastWindow to true
            if ackNum in range(segments - window, segments + 1):
                lastWindowAck = True
            # If the acked sequence number is equal to the base:
            if ackNum == base:
                allAcked = True
                # Check if each packet in the current window has been acknowledged, the first one we find
                # ...That hasn't been acked set allAcked to false,  the new base to this sequence number and
                # ...break the loop
                for pkt in range(base, seq_No):
                    if pkt not in acknowledged:
                        base = pkt
                        allAcked = False
                        break
                # If all in the window have been correctly acked, update the base and tiemr
                if allAcked:
                    base = seq_No
                    isTimer = False
                # Otherwise set the timer
                else:
                    isTimer = True
                    clock = perf_counter()


# Timeout thread keeps track of the retry timeout and when to retransmit packets
def timeOut():
    # Instantiate the global variables we will use
    global base
    global finished
    global lock
    global acknowledged
    global clock
    global lastWindowRetransmissions
    global timeout
    global isTimer
    global seq_No
    global lastWindowAck
    global prevWindowCount

    # Until transmission has finished:
    while not finished:
        # Note the current time
        currentTime = perf_counter()
        # Acquire the lock
        with lock:
            # If the timer isn't set then continue loop
            if not isTimer:
                continue
            # If timer is less than timeout (timer hasn't timed out), continue loop
            if currentTime - clock < timeout:
                continue
            # Otherwise reset the timer
            else:
                clock = perf_counter()
            # If all packets have been sent and acknowledged set finished to True, breaking the loop
            if segments == len(acknowledged):
                finished = True
                break
            # If
            if prevWindowCount == lastWindowRetransmissions:
                finished = True
                break
            if lastWindowAck:
                prevWindowCount += 1
            # Resend the packets in the window:
            temp_base = base
            increment = 0
            # While current packet were looking at is in resend window
            while base + increment < seq_No and base + increment < len(fullPackets):
                # If packet hasn't been acknowledged resend it to the socket
                if base + increment not in acknowledged:
                    s.sendto(fullPackets[base + increment], (host, port))
                increment += 1


clock = perf_counter()
# Create thread instances of receive and timeour threads, with daemon set to true allowing the program to exit
receiveThread = Thread(target=receive, daemon=True)
timeOutThread = Thread(target=timeOut, daemon=True)
# Note the start time
start_time = perf_counter()
# Start both threads
receiveThread.start()
timeOutThread.start()

# Until we have successfully sent and acked all packets
while not finished:
    # If we've acknowledged all packets set finished to True
    if segments == len(acknowledged):
        with lock:
            finished = True
    if prevNotQueued == segments:
        continue
    # Attempt to send current packet, if successful increment current packet by one
    if send(prevNotQueued == segments - 1):
        prevNotQueued += 1
# Close the socket
s.close()
# Calculate the time taken to transfer the file and the file size in kilobytes then calculate and print throughput
transfer_time = perf_counter() - start_time
file_size = file_size = len(data) / 1000
throughput = round(file_size / transfer_time)
print(throughput)





