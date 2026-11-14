# Done by member 1 - Rami Ayoub 202504559
import hashlib
import struct

# Shared packet types used by both sender and receiver which we agreed on
DATA, ACK, END = 1, 2, 3
# Network byte order: type (1 byte), sequence (4), length (2).
HEADER = struct.Struct("!BIH")
CHUNK_SIZE = 1024


def encode_packet(packet_type, seq, data=b""):# here we create a packets (and check if its header is valid too)
    """Pack type (1 byte), sequence (4 bytes), length (2 bytes), payload."""
    if packet_type not in (DATA, ACK, END):#this checks the packet type
        raise ValueError("Unknown packet type")
    if not 0 <= seq <= 0xFFFFFFFF:#the sequence number is 4bytes
        raise ValueError("Sequence out of range")
    if len(data) > 65535:#the length is 2 bytes
        raise ValueError("Payload too long")
    if packet_type == ACK and data:#ack shouldnt contain data
        raise ValueError("ACK must have no payload")
    if packet_type == END and len(data) != 32:#sha-256 produces a 32 byte binary hash
        raise ValueError("END must contain the 32-byte SHA-256 digest")
    # this Converts header fields to bytes then add the payload
    return HEADER.pack(packet_type, seq, len(data)) + data


def decode_packet(packet):# here we open the packet and read it
    """Return (packet_type, sequence_number, payload)."""
    if len(packet) < HEADER.size:#we check that the packet contains atleast 7 bytes (header)
        raise ValueError("Incomplete header")
    # Read the header and extract the payload after the first seven bytes.
    packet_type, seq, length = HEADER.unpack_from(packet)
    data = packet[HEADER.size:]# take everything after the header
    if len(data) != length:# this checks if amount of data we have matches the length written in the header
        raise ValueError("Invalid payload length")
    # Reuse validation for known types and control packet lengths
    encode_packet(packet_type, seq, data)
    return packet_type, seq, data


def build_packets(filename, chunk_size=CHUNK_SIZE):# in here we take the file and split it into paackets
    """Return a list of DATA packets followed by a sequenced END packet."""
    if not 1 <= chunk_size <= CHUNK_SIZE:
        raise ValueError("Chunk size must be between 1 and 1024")
    packets = [] # this is where we will store all the packets
    digest = hashlib.sha256()  # this is an Incremental hash of the original file
    with open(filename, "rb") as source:
        while True:
            chunk = source.read(chunk_size)# read 1024 bytes at a time
            if not chunk:
                break# stop if there is nothing to read
            # next we update the hash and assign the next sequence number
            digest.update(chunk)
            packets.append(encode_packet(DATA, len(packets), chunk))#we call the function we did before that creates packets and add it to the list
    # this is the END packet that follows every DATA packet and carries the raw digest
    packets.append(encode_packet(END, len(packets), digest.digest()))
    return packets #member 2 should use this list

# now member 2 recieves the list of packets and choose a window size and send the packets through my unreliable channel
# so member 2 should call my unreliable channel and send the data
# i will make a unreliable channel that will drop and reorder data as a simulation to check if what we did is reliable
