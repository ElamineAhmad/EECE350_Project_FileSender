from unreliable_channel import UnreliableChannel
from packets import decode_packet, ACK, build_packets
import socket
import os
import time

# Done by member 2: Yara Sleem
# AI assisted debugging and review
class Sending_Window:
    def __init__(self, N, packets, sock, address, loss, reorder): 
        if N<=0: 
            raise ValueError("Sending window length has to be positive")
        self.N = N #size of the sending window
        self.base = 0 #oldest unacknowledged packet
        self.next_packet = 0 #next packet to be sent
        self.state = {} #this is a dictionary that keeps track of the state of every packet in the packets list
        self.packets = packets #packets to be sent
        self.sock = sock 
        self.address = address # address to send to 
        self.duplicated_ack_number = 0 #counter to keep track of the number of duplicate acks
        self.timeout = 0.5 #initial timeout
        self.timeouts = 0 #number of timeouts
        self.transmissions = 0 #number of transmissions
        self.retransmissions = 0 #number of retransmissions
        self.starting_time = time.monotonic() #starting time to later compute transmission time
        self.timer_start=None #variable that will be used to check for timeout
        self.transfer_time = 0 #total time to transfer all the packets
        self.Unreliable_Channel = UnreliableChannel(self.sock, self.address, loss, reorder) #creating an instace of UnreliableChannel in order to send through it and not directly through UDP
        self.estimated_rtt = None 
        self.dev_rtt = 0
        self.send_times = {} # dictionary to keep track of the sending time of every packet


    def check_timeout(self): #checks if a timeout occurred
        if (self.timer_start is not None) and (time.monotonic() - self.timer_start >= self.timeout): #detected timeout
            print(f"TIMEOUT {self.base}, RETRANSMIT {self.base}")
            self.timeouts += 1 
            self.retransmissions += 1 #updated the counters
            self.Unreliable_Channel.send(self.packets[self.base]) #retransmitted the oldest unacked packet (base)
            self.state[self.base] = "retransmitted" #change the state
            self.timeout = min(self.timeout * 2, 2.0) #exponential timeout as in TCP capped at 2
            self.timer_start = time.monotonic() #restart the time
    def send(self):
        sent_something =False # to avoid printing the window uneccesarily
        while self.next_packet<self.base+self.N and self.next_packet<len(self.packets): #if we have space in the window and we still have packets to send
            if self.base == self.next_packet: # if all packets have been acked, then the one we'll send now will be the oldest unacked one
                self.timer_start = time.monotonic() # start timer
            self.Unreliable_Channel.send(self.packets[self.next_packet]) #send the next packet
            self.send_times[self.next_packet] = time.monotonic() #store the time when we sent the packet
            self.state[self.next_packet] = "sent" 
            self.next_packet+=1 
            self.transmissions+=1 
            sent_something=True
        if sent_something:
            self.show_window()
        self.transfer_time = time.monotonic()-self.starting_time 

    def receive(self, raw):
        packagetype, ack, data = decode_packet(raw)
        if packagetype!=ACK: #not of type ACK, then this is not an acknowledgement
            return
        if ack==self.base: #recieved ack that we've already recieved, base is still not acked yet
            self.duplicated_ack_number+=1
            if self.duplicated_ack_number==3: #three duplicate acks
                print(f"3 DUP ACKS, RETRANSMIT {ack}")
                self.Unreliable_Channel.send(self.packets[ack]) #retransmitting
                self.state[ack] = "retransmitted" 
                self.retransmissions+=1
                return
    
        if ack>self.base: #recieved a new ack
            print(f"ACK {ack}")
            last = ack - 1 #last recieved sequence number 
            if all(self.state[s] != "retransmitted" for s in range(self.base, ack)): #only measure RTT if no packet covered by this ACK was retransmitted
                sample = time.monotonic() - self.send_times[last] #sample rtt , ie time from sending this packet until its ACK arrived
                if self.estimated_rtt is None: #happens in the first measurement
                    self.estimated_rtt, self.dev_rtt = sample, sample / 2
                else:
                    self.estimated_rtt = 0.875*self.estimated_rtt + 0.125*sample # EstimatedRTT: moving average, new sample weighted 1/8
                    self.dev_rtt = 0.75*self.dev_rtt + 0.25*abs(sample - self.estimated_rtt)# DevRTT: how much the RTT varies, weighted 1/4
            
            if self.estimated_rtt is not None:
                self.timeout = min(2, max(0.05, self.estimated_rtt + 4*self.dev_rtt))  
            else:
                self.timeout = 0.5  #no RTT measured yet, so we go back to the initial timeout

            for s in range(self.base, ack): #recieved a cumulative ack, then all the ones before is are acked
                self.state[s] = "acked" 
            self.base=ack #base is now the oldest unacked packet

            if self.base < len(self.packets): #check to avoid printing an empty window
                self.show_window()

            if self.base == self.next_packet: #all of the packets are acked 
                self.timer_start = None
            else: #there aer still packets waiting to be acked, then timer should be started
                self.timer_start = time.monotonic()
            self.duplicated_ack_number=0

    def summary(self): #Display the summary
        return {"Transmissions:  ": self.transmissions,
            "Retransmissions:": self.retransmissions,
            "Timeouts:       ": self.timeouts,
            "Transfer time:   ": self.transfer_time,
            "Channel:        ": self.Unreliable_Channel.summary()}

    def show_window(self):  # live view of the sending window
        last = min(self.base + self.N, len(self.packets)) - 1
        states = " ".join(f"{s}:{self.state.get(s, 'not sent')}" for s in range(self.base, last + 1))
        print(f"WINDOW [{self.base}–{last}]  {states}")



packets = build_packets("test.txt") 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.02)
window = Sending_Window(8, packets, sock, ("127.0.0.1", 5000), 0.1, 0.2)

print("File: test.txt", os.path.getsize("test.txt"), "bytes")
print("Packets:", len(packets))
print("N: 8   Loss: 0.1   Reorder: 0.2")

while window.base < len(packets):
    window.send()
    try:
        window.receive(sock.recvfrom(2048)[0])
    except (socket.timeout,ConnectionResetError, ConnectionRefusedError):
        pass
    window.check_timeout()
window.transfer_time = time.monotonic() - window.starting_time

print("SUMMARY:")
for name, value in window.summary().items():
    print(name, value)


