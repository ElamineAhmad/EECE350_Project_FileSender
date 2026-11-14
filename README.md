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
