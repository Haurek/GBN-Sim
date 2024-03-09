import random
import struct

WINDOW_SIZE = 3
TIMEOUT = 10
LOSS_RATE = 0.1
RECV_BUFFER = 4096


def calcChecksum(data):
    # calculate checksum from packet
    checksum = 0
    for i in range(len(str(data))):
        checksum += int.from_bytes(bytes(str(data)[i], encoding='utf-8'), byteorder='little', signed=False)
        checksum &= 0xff
    return checksum


def notCorrupt(checksum, data):
    if checksum == calcChecksum(data):
        print("Not Corrupt")
        return True
    else:
        print("Corrupt")
        return False


class GBNReceiver:
    """GBN Receiver Class"""

    def __init__(self, recv_socket, out):
        self.recvSocket = recv_socket
        self.timeout = TIMEOUT
        self.lossRate = LOSS_RATE
        self.expextSeq = 0
        self.sndpkt = self.make_pkt(0, 0)
        self.address = None
        self.outputFile = out

    def udt_send(self, pkt):
        if self.lossRate == 0 or random.randint(0, int(1 / self.lossRate)) != 1:
            self.recvSocket.sendto(pkt, self.address)
            print('Receiver send ACK:', pkt[1])
        else:
            print('Receiver send ACK:', pkt[1], ', but lost.')

    def make_pkt(self, expectedseqnum, ack):
        print("make pkt, expected num is ", expectedseqnum, "ack is ", ack)
        return struct.pack("BB", expectedseqnum, ack)

    def extract_data(self, pkt):
        # pkt[0] -> seqnum
        # pkt[1] -> checksum
        # pkt[2:] -> data
        return pkt[0], pkt[1], pkt[2:]

    def deliver_data(self, data):
        self.outputFile.write(data)

    def rdt_rcv(self):
        pkt, addr = self.recvSocket.recvfrom(RECV_BUFFER)
        self.address = addr
        seqnum, checknum, data = self.extract_data(pkt)
        print("receive pkt seq ", seqnum, "Receiver expected seq ", self.expextSeq)
        if seqnum == self.expextSeq and notCorrupt(checknum, data):
            self.deliver_data(data)
            self.expextSeq = (self.expextSeq + 1) % 256
            print("change expected seq to ", self.expextSeq)
            self.sndpkt = self.make_pkt(self.expextSeq, seqnum)
            self.udt_send(self.sndpkt)
            return True
        else:
            return False

    def run(self):
        while True:
            if not self.rdt_rcv():
                # default
                self.udt_send(self.sndpkt)
