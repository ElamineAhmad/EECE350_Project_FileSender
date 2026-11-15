# EECE350_Project_FileSender
Reliable file transfer over UDP that splits a file into packets , simulates loss and reordering, and uses a sliding window acknowledgement and retransmission to deliver the complete file intact and in order.

Packet Preparation (packets.py) done by member 1 - Rami Ayoub

what it does:
- Reads the original file in binary mode.
- Splits the file into chunks of up to 1024 bytes.
- Encodes and decodes packets using the struct library.
- Assigns sequence numbers starting from 0.
- Creates an END packet containing the SHA-256 hash of the original file.

Unreliable Channel (unreliable_channel.py) done by member 1 - Rami Ayoub

what it does:
- Simulates packet loss and reordering.
- Temporarily holds packets to change their transmission order.
- Sends packets through a UDP socket.
- Handles initial transmissions and retransmissions.
- Counts attempted, sent, dropped and reordered packets.

The shared packet format that all members agreed on:

1.The header uses the !BIH format with a total size of 7 bytes.

explanation:
- Packet type: 1 byte.
- Sequence number: 4 bytes.
- Payload length: 2 bytes.
- Payload: variable size.

2.The shared Conventions:

explanation:
- DATA = 1, ACK = 2, END = 3.
- Default chunk size = 1024 bytes.
- Sequence numbers start at 0.
- ACK contains the next expected sequence number with an empty payload.
- END follows the last DATA packet and contains the raw 32-byte SHA-256 hash.
- Loss and reorder probabilities are between 0 and 1, and their sum cannot exceed 1.

3.The Common Methods:

explanation:
- build_packets(filename): Returns the list of DATA and END packets.
- encode_packet(packet_type, seq, data=b""): Creates an encoded packet.
- decode_packet(packet): Returns the packet type, sequence number and payload.
- UnreliableChannel(sock, address, loss, reorder): Initializes the simulator.
- channel.send(packet): Attempts to transmit a packet.
- channel.summary(): Returns channel statistics.

How member 1 Rami Ayoub Integrated with Member 2 Yara Sleem:

- Uses build_packets(filename) to prepare packets.
- Uses decode_packet(packet) to read ACKs.
- Uses channel.send(packets[seq]) for all transmissions and retransmissions.
- Manages the sliding window, timers and retransmissions.
- Starts the protocol timer even when a packet is dropped or held.

How member 1 Rami Ayoub Integrated with Member 3 Ahmad Al Amine:

- Uses decode_packet(packet) to read received packets.
- Uses encode_packet(ACK, expected) to create cumulative ACKs.
- Handles duplicate and out-of-order packets.
- Uses hashlib.sha256(file_data).digest() to verify file integrity.

Settings

- chunk_size: Maximum file chunk size, 1024 bytes by default.
- loss: Probability of dropping a packet.
- reorder: Probability of selecting a packet for reordering.

Requirements

Python 3. No additional libraries are required.


Sending Packets: Done by Member 2: Yara Sleem ID:202601169

what it does: manages sending the packets:
 - keeps track of a sending window of N packets, the base (oldest unacknowledged packet), the next packet to send, the state of each packet, the sending time of each packet
 - runs a timer for the oldest unacknowledged packet and retransmits it on timeout.
 - retransmits a packet after 3 duplicate ACKs
 - estimates the timeout like TCP: TimeoutInterval = EstimatedRTT + 4*DevRTT, (no RTT sample from retransmitted packets) and exponential backoff (doubled on timeout, capped at 2 s).
 - sends and retransmits every packet, including END, through member 1's UnreliableChannel, never directly over the socket.
 - counts transmissions, retransmissions, timeouts and total transfer time.
 - has a function summary that returns a dictionary transmissions, retransmissions, timeouts, transfer time, and the summary of the channel written by member 1 Rami Ayoub

Display:
- settings at start: file name and size, number of packets, N, loss and reorder.
- live window view, e.g. WINDOW [14–21] 14:retransmitted 15:sent ...
- events: ACK x, TIMEOUT x, RETRANSMIT x, 3 DUP ACKS, RETRANSMIT x.
- summary at the end: transmissions, retransmissions, timeouts, transfer time and the channel statistics from channel.summary().

Implementation:
Class Sending_Window(N, packets, sock, address, loss, reorder), where sock is a UDP socket and address is the receiver's (IP, port).
Methods:
- send(): sends new packets while the window has room.
- receive(raw): handles an ACK (new ACK, duplicate ACK or fast retransmit).
- check_timeout(): retransmits base if its timer expired.
- show_window(): prints the current window and packet states.
- summary(): returns transmissions, retransmissions, timeouts, transfer time and the channel summary.

How to run the sender:
1. Start the receiver first (member 3).
2. python sender.py
The sender reads test.txt and sends to 127.0.0.1:5000 (matches the receiver's port).

Settings:
- N: window size, the number of packets that can be sent but not yet acknowledged.
- timeout: starts at 0.5 s, then follows the RTT estimate (between 0.05 s and capped at 2 s).
- loss and reorder (explained in member 1's Settings section).
  
Uses build_packets and decode_packet from packets.py and UnreliableChannel from unreliable_channel.py (member 1).

Requirements: Python 3, no additional libraries (socket, time, os from the standard library).
