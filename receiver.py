# Done by member 3 - Ahmad El Amine - 202600699
# Receiver and acknowledgements (written with help from an AI assistant, reviewed in detail by Ahmad)
#
# Run:  python receiver.py [output_file] [--host 127.0.0.1] [--port 5000] [--linger 3]
import argparse
import hashlib
import os
import socket
import sys
import time

from packets import DATA, ACK, END, encode_packet, decode_packet  # shared code from member 1

# ---------------------------------------------------------------- display helpers
# ANSI colour codes for a colour-coded terminal log
GREEN, YELLOW, CYAN, RED, MAGENTA, BOLD, RESET = (
    "\033[92m", "\033[93m", "\033[96m", "\033[91m", "\033[95m", "\033[1m", "\033[0m")

if os.name == "nt":
    os.system("")  # this turns on ANSI colour support in the Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8")  # so the arrow character prints correctly
except AttributeError:
    pass


def log(colour, text):
    """Print one event line with a timestamp, e.g. '[20:06:23] RECV 12 in order → ACK 13'."""
    print(f"{colour}[{time.strftime('%H:%M:%S')}] {text}{RESET}", flush=True)


# ---------------------------------------------------------------- receiver
class Receiver:
    def __init__(self, sock, output_file, linger=3.0):
        self.sock = sock
        self.output_file = output_file
        self.linger = linger      # seconds to keep answering after END, in case our last ACK was lost
        self.expected = 0         # next in-order sequence number we are waiting for
        self.buffer = {}          # out-of-order packets: seq -> (type, payload)
        self.chunks = []          # in-order DATA payloads, used to rebuild the file
        self.end_hash = None      # SHA-256 digest carried by the END packet
        self.done = False         # becomes True once END is delivered in order
        # statistics for the summary
        self.received = 0
        self.in_order = 0
        self.out_of_order = 0
        self.duplicates = 0
        self.acks_sent = 0
        self.dup_acks_sent = 0
        self.resent_acks = 0

    def send_ack(self, address, kind="normal"):
        """Send a cumulative ACK carrying the next expected sequence number."""
        self.sock.sendto(encode_packet(ACK, self.expected), address)
        self.acks_sent += 1
        if kind == "dup":
            self.dup_acks_sent += 1
        elif kind == "resent":
            self.resent_acks += 1

    def deliver(self, packet_type, data):
        """Accept one packet in order and advance 'expected'."""
        if packet_type == DATA:
            self.chunks.append(data)
        elif packet_type == END:
            self.end_hash = data
            self.done = True
        self.expected += 1

    def handle(self, packet, address):
        """Process one received UDP datagram according to the cumulative-ACK rules."""
        try:
            packet_type, seq, data = decode_packet(packet)
        except ValueError as error:          # corrupted or malformed datagram
            log(RED, f"BAD PACKET ignored ({error})")
            return
        if packet_type == ACK:               # a receiver should never get ACKs
            return
        self.received += 1
        name = "END " if packet_type == END else ""

        # Case 1: duplicate packet (already delivered, or already sitting in the buffer)
        if seq < self.expected or seq in self.buffer:
            self.duplicates += 1
            self.send_ack(address, kind="resent")
            log(MAGENTA, f"RECV {name}{seq} duplicate, discarded \u2192 ACK {self.expected}")

        # Case 2: in-order packet (it may also fill a gap)
        elif seq == self.expected:
            self.in_order += 1
            self.deliver(packet_type, data)
            filled = 0
            # pull every buffered packet that now follows in order
            while self.expected in self.buffer:
                self.deliver(*self.buffer.pop(self.expected))
                filled += 1
            self.send_ack(address, kind="normal")
            if filled:
                log(CYAN, f"RECV {name}{seq} fills gap (+{filled} buffered) \u2192 ACK {self.expected}")
            else:
                log(GREEN, f"RECV {name}{seq} in order \u2192 ACK {self.expected}")

        # Case 3: out-of-order packet (a gap: something before it was lost or delayed)
        else:
            self.out_of_order += 1
            self.buffer[seq] = (packet_type, data)
            self.send_ack(address, kind="dup")
            log(YELLOW, f"RECV {name}{seq} out of order, buffered \u2192 DUP ACK {self.expected}")

    def run(self):
        """Main loop: receive until END is delivered, then linger to re-ACK late retransmissions."""
        self.sock.settimeout(0.5)
        start = None
        last_packet = time.time()
        while True:
            try:
                packet, address = self.sock.recvfrom(65535)
            except socket.timeout:
                # after END, stop once the sender has been quiet for 'linger' seconds
                if self.done and time.time() - last_packet >= self.linger:
                    break
                continue
            except ConnectionResetError:     # Windows reports ICMP "port unreachable" this way
                continue
            if start is None:
                start = time.time()
            last_packet = time.time()
            was_done = self.done
            self.handle(packet, address)
            if self.done and not was_done:
                self.finish(time.time() - start)
                log(BOLD, f"Waiting {self.linger}s in case the final ACK was lost...")
        self.print_summary()

    def finish(self, elapsed):
        """Reassemble the file, write it to disk and verify its SHA-256 hash."""
        file_data = b"".join(self.chunks)
        with open(self.output_file, "wb") as out:
            out.write(file_data)
        self.elapsed = elapsed
        self.size = len(file_data)
        self.match = hashlib.sha256(file_data).digest() == self.end_hash
        log(BOLD, f"FILE WRITTEN {self.output_file} ({self.size} bytes, {elapsed:.2f}s)")
        if self.match:
            log(GREEN + BOLD, "SHA-256 MATCH \u2714 file received intact")
        else:
            log(RED + BOLD, "SHA-256 MISMATCH \u2718 file is corrupted")

    def print_summary(self):
        print(f"\n{BOLD}========== RECEIVER SUMMARY =========={RESET}")
        print(f"Output file          : {self.output_file} ({self.size} bytes)")
        print(f"Packets received     : {self.received}")
        print(f"  in order           : {self.in_order}")
        print(f"  out of order       : {self.out_of_order} (buffered)")
        print(f"  duplicates         : {self.duplicates} (discarded)")
        print(f"ACKs sent            : {self.acks_sent} "
              f"({self.dup_acks_sent} dup ACK, {self.resent_acks} re-sent)")
        print(f"Transfer time        : {self.elapsed:.2f}s")
        verdict = f"{GREEN}MATCH{RESET}" if self.match else f"{RED}MISMATCH{RESET}"
        print(f"Integrity (SHA-256)  : {verdict}")


def main():
    parser = argparse.ArgumentParser(description="Reliable UDP file receiver (member 3)")
    parser.add_argument("output", nargs="?", default="received_test.txt",
                        help="where to save the received file (default: received_test.txt)")
    parser.add_argument("--host", default="127.0.0.1", help="IP address to listen on")
    parser.add_argument("--port", type=int, default=5000, help="UDP port to listen on")
    parser.add_argument("--linger", type=float, default=3.0,
                        help="seconds to keep re-ACKing after END in case the last ACK was lost")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"{BOLD}Receiver listening on {args.host}:{args.port}, saving to {args.output}{RESET}")
    try:
        Receiver(sock, args.output, args.linger).run()
    finally:
        sock.close()


if __name__ == "__main__":
    main()
