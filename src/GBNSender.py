import random
import socket
import struct
import time

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


class GBNSender:
    """GBN Sender Class"""
    def __init__(self, sender_socket, addr, file):
        # init
        self.senderSocket = sender_socket
        self.address = addr
        self.file = file
        self.windowSize = WINDOW_SIZE
        self.timeout = TIMEOUT
        self.lossRate = LOSS_RATE
        self.base = 0
        self.nextSeq = 0
        self.dataList = []
        self.packets = [None] * 256

        while True:
            data = file.read(2048)
            if len(data) <= 0:
                break
            self.dataList.append(data)

    def udt_send(self, pkt):
        # add data to packets
        self.packets[pkt[0]] = pkt
        # send udp packet
        if self.lossRate == 0 or random.randint(0, int(1 / self.lossRate)) != 1:
            self.senderSocket.sendto(pkt, self.address)
            print("send packet ", pkt[0], "successfully")
        else:
            print("send packet ", pkt[0], "but Packet lost.")
        time.sleep(0.2)

    def make_pkt(self, data):
        # make udp packet
        print("make pkt", self.nextSeq)
        return struct.pack('BB', self.nextSeq, calcChecksum(data)) + data

    def rdt_rcv(self):
        terminal = 0
        while True:
            # terminal while timeout 10 times
            if terminal >= 5:
                print("Terminal!")
                return False
            try:
                pkt, addr = self.senderSocket.recvfrom(RECV_BUFFER)
                expect_seq = pkt[0]
                ack = pkt[1]
                print("receive ack ", ack)
                if self.base == expect_seq:
                    # drop duplicate packet
                    print("drop duplicate packet")
                    pass

                self.base = (ack + 1) % 256

                if self.base == self.nextSeq:
                    # finish
                    self.stop_timer()
                else:
                    # restart timer
                    self.start_timer()

                return True

            except socket.timeout:
                print("Timeout!")
                for i in range(self.base, self.nextSeq):
                    print("resend pkt ", i)
                    self.udt_send(self.packets[i])
                terminal += 1

    def start_timer(self):
        print("start timer")
        self.senderSocket.settimeout(self.timeout)

    def stop_timer(self):
        print("stop timer")
        self.senderSocket.settimeout(None)

    def rdt_send(self, data):
        if self.nextSeq < self.base + self.windowSize:
            sndpkt = self.make_pkt(data)
            self.udt_send(sndpkt)
            if self.base == self.nextSeq:
                self.start_timer()
            # cache pkt for resend
            self.packets[self.nextSeq] = sndpkt
            self.nextSeq = (self.nextSeq + 1) % 256
            print("nextSeq=", self.nextSeq)
            return True
        else:
            print("refuse data")
            return False

    # def run(self):
    #     data_num = 0
    #     while True:
    #         print("send data at list ", data_num)
    #         if len(self.dataList) > 0 and self.rdt_send(self.dataList[data_num]):
    #             data_num += 1
    #             if data_num >= len(self.dataList):
    #                 print("finish send")
    #                 return
    #
    #         elif not self.rdt_rcv():
    #             # close
    #             print("close socket")
    #             self.senderSocket.close()

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

