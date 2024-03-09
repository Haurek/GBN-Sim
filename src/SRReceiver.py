import random
import socket
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


class SRReceiver:
    """SR Receiver Class"""

    def __init__(self, recv_socket, out):
        self.recvSocket = recv_socket
        self.timeout = TIMEOUT
        self.windowSize = WINDOW_SIZE
        self.lossRate = LOSS_RATE
        self.rcv_base = 0
        self.address = None
        self.outputFile = out
        # for base update
        self.recvCheck = [False] * 256
        # cache receive packets
        self.recvPackets = [None] * 256

    def udt_send(self, pkt):
        if self.lossRate == 0 or random.randint(0, int(1 / self.lossRate)) != 1:
            self.recvSocket.sendto(pkt, self.address)
            print('Receiver send ACK:', pkt[0])
        else:
            print('Receiver send ACK:', pkt[0], ', but lost.')

    def make_pkt(self, ack):
        print("make pkt, ack is ", ack)
        return struct.pack("B", ack)

    def extract_data(self, pkt):
        # pkt[0] -> seq
        # pkt[1] -> checksum
        # pkt[2:] -> data
        return pkt[0], pkt[1], pkt[2:]

    def deliver(self):
        print("deliver data")
        while True:
            # deliver data and update base
            data = self.recvPackets[self.rcv_base]
            self.outputFile.write(data)
            self.unmark(self.rcv_base)
            self.rcv_base = (self.rcv_base + 1) % 256
            if not self.recvCheck[self.rcv_base]:
                break
        print("update rcv_base to ", self.rcv_base)

    def mark(self, seq):
        self.recvCheck[seq] = True

    def unmark(self, seq):
        self.recvCheck[seq] = False

    def rdt_rcv(self):
        pkt, addr = self.recvSocket.recvfrom(RECV_BUFFER)
        self.address = addr
        seq, checksum, data = self.extract_data(pkt)
        print("receive pkt seq ", seq)
        if seq < self.rcv_base + self.windowSize and notCorrupt(checksum, data):
            # receive pkt at window and not corrupt
            self.recvPackets[seq] = data
            if seq == self.rcv_base:
                self.deliver()
            snd_pkt = self.make_pkt(seq)
            # mark pkt
            self.mark(seq)
            # send ack
            self.udt_send(snd_pkt)
            return True
        else:
            return False

    def run(self):
        while True:
            if not self.rdt_rcv():
                # default, drop the pkt
                continue
