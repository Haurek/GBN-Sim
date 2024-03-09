import random
import socket
import struct
import time
import threading

WINDOW_SIZE = 3
TIMEOUT = 5
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


class SRSender:
    """GBN Sender Class"""

    def __init__(self, sender_socket, addr, file):
        # init
        self.senderSocket = sender_socket
        self.address = addr
        self.file = file
        self.windowSize = WINDOW_SIZE
        self.timeout = TIMEOUT
        self.lossRate = LOSS_RATE
        self.send_base = 0
        self.nextSeq = 0
        self.dataList = []
        # cache packets for resend
        self.packets = [None] * 256
        self.rcvCheck = [False] * 256
        self.timers = {}

        # fill dataList
        while True:
            data = file.read(2048)
            if len(data) <= 0:
                break
            self.dataList.append(data)

    def udt_send(self, pkt):
        # unmark pkt
        self.unmark(pkt[0])
        # set timer
        self.start_timer(pkt[0])
        # send udp packet
        if self.lossRate == 0 or random.randint(0, int(1 / self.lossRate)) != 1:
            self.senderSocket.sendto(pkt, self.address)
            print("send packet ", pkt[0], "successfully")
        else:
            print("send packet ", pkt[0], "but Packet lost.")
        time.sleep(0.2)

    def make_pkt(self, data):
        # make packet
        print("make pkt", self.nextSeq)
        return struct.pack('BB', self.nextSeq, calcChecksum(data)) + data

    def rdt_rcv(self):
        terminal = 0
        while True:
            self.senderSocket.settimeout(self.timeout)
            try:
                # receive ack from server
                pkt, addr = self.senderSocket.recvfrom(RECV_BUFFER)
                # self.address = addr
                ack = pkt[0]
                print("receive ack ", ack)
                # mark for base update
                self.mark(ack)
                # stop pkt timer while receive ack pkt
                self.stop_timer(ack)
                print("stop timer ", ack)
                if self.send_base == ack:
                    # update send_base
                    while True:
                        self.send_base = (self.send_base + 1) % 256
                        if not self.rcvCheck[self.send_base]:
                            print("update send_base ", self.send_base)
                            break
                return True
            except socket.timeout:
                # close connect if timeout more than 5 times
                terminal += 1
                if terminal >= 5:
                    return False

    def start_timer(self, seq):
        print("start timer ", seq)
        timer = self.set_timer(seq)
        timer.start()
        self.timers[seq] = timer

    def stop_timer(self, seq):
        timer = self.timers[seq]
        timer.cancel()

    def resend(self, seq):
        # resend pkt seq
        print("Timeout!")
        self.stop_timer(seq)
        print("resent pkt", seq)
        self.udt_send(self.packets[seq])

    def set_timer(self, seq):
        # create timer for seq pkt
        return threading.Timer(self.timeout, function=self.resend, args=(seq,))

    def mark(self, seq):
        self.rcvCheck[seq] = True

    def unmark(self, seq):
        self.rcvCheck[seq] = False

    def rdt_send(self, data):
        if self.nextSeq < self.send_base + self.windowSize:
            # have pkts to send
            sndpkt = self.make_pkt(data)
            # cache pkt for resend
            self.packets[self.nextSeq] = sndpkt
            # send pkt
            self.udt_send(sndpkt)
            # update next seq
            self.nextSeq = (self.nextSeq + 1) % 256
            print("nextSeq =", self.nextSeq)
            return True
        else:
            print("refuse data")
            return False

    def run(self):
        data_num = 0
        while True:
            if data_num < len(self.dataList) and self.rdt_send(self.dataList[data_num]):
                data_num += 1
            elif not self.rdt_rcv():
                break

        # close
        print("close socket")
        self.senderSocket.close()
