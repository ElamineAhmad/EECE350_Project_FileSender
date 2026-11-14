#done by memebr 1 Rami Ayoub 202504559
import random
from packets import decode_packet #because we want to read the seq number in the terminal

class UnreliableChannel:

    def __init__(self, sock, address, loss=0.1, reorder=0.2,
                 rng=None, log=print):
        if not (0 <= loss <= 1 and 0 <= reorder <= 1
                and loss + reorder <= 1):
            raise ValueError("Probabilities must be in [0,1] and sum to <= 1")#checks for invalid arguments in the constructor
        self.sock = sock
        self.address = address # receiver ip adress and port
        self.loss = loss # this is probability of losing a packet
        self.reorder = reorder # this is probability for selecting packets for reordering
        self.rng = rng if rng is not None else random.Random() # this is random number generator
        self.log = log 
        self.pending = None  # At most one held packet.
        self.attempted = 0
        self.sent = 0
        self.dropped = 0
        self.reordered = 0

    def _send_udp(self, packet):
        self.sock.sendto(packet, self.address)# this sends the packet to the receiver using UDP
        self.sent += 1 # this increment the udp transmission
        self.log(f"UDP SEND {decode_packet(packet)[1]}")# this prints the packets sequence number

    def send(self, packet): 
        """Simulate loss/reordering, then transmit using UDP as appropriate."""
        _, seq, _ = decode_packet(packet)
        self.attempted += 1
        r = self.rng.random()

        if r < self.loss: # we drop the packet s the packet is lost 
            self.dropped += 1
            self.log(f"DROPPED {seq} (simulated)")
            return

        if self.pending is not None: # if packet 2 is already stored in pending and member 2 gives me packet 3 i send 3 then 2 so i reorder packets
            old = self.pending
            self._send_udp(packet)
            self._send_udp(old)
            self.pending = None
            self.log(f"REORDERED {decode_packet(old)[1]} after {seq}")

        elif r < self.loss + self.reorder:# here we dont send the packet we store it inside pending so we use it later to reorder
            self.pending = packet
            self.reordered += 1
            self.log(f"HELD {seq} (simulated reordering)")
        else:# here is the last case were we send the packets normally
            self._send_udp(packet)

    def summary(self): # this member 2 must use it
        return {"attempted": self.attempted,
                "udp_sent": self.sent,
                "dropped": self.dropped,
                "reordered": self.reordered,
                "pending": int(self.pending is not None)}
