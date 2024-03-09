from socket import *
import threading

import GBNSender
import GBNReceiver


def receive_thread(connectSocket, fp):
    receiver = GBNReceiver.GBNReceiver(connectSocket, fp)
    receiver.run()


def send_thread(connectSocket, addr, fp):
    sender = GBNSender.GBNSender(connectSocket, addr, fp)
    sender.run()


sendName1 = '127.0.0.1'
sendPort1 = 12000
sendSocket1 = socket(AF_INET, SOCK_DGRAM)
address1 = (sendName1, sendPort1)
# file send to port 12000
send_fp1 = open('../lab6/screen1.jpg', 'rb')

receiveName1 = ''
receivePort1 = 12001
receiverSocket1 = socket(AF_INET, SOCK_DGRAM)
receiverSocket1.bind((receiveName1, receivePort1))
# file send to port 12000
receiver_fp1 = open("./receive/GBNReceive1.jpg", 'wb')

sender_thread1 = threading.Thread(target=send_thread, args=(sendSocket1, address1, send_fp1, ))
receiver_thread1 = threading.Thread(target=receive_thread, args=(receiverSocket1, receiver_fp1, ))

sendName2 = '127.0.0.1'
sendPort2 = 12001
sendSocket2 = socket(AF_INET, SOCK_DGRAM)
address2 = (sendName2, sendPort2)
# file send to port 12001
send_fp2 = open('../lab6/screen2.jpg', 'rb')

receiveName2 = ''
receivePort2 = 12000
receiverSocket2 = socket(AF_INET, SOCK_DGRAM)
receiverSocket2.bind((receiveName2, receivePort2))
# file receive from port 12000
receiver_fp2 = open("./receive/GBNReceive2.jpg", 'wb')

sender_thread2 = threading.Thread(target=send_thread, args=(sendSocket2, address2, send_fp2, ))
receiver_thread2 = threading.Thread(target=receive_thread, args=(receiverSocket2, receiver_fp2, ))

receiver_thread1.start()
receiver_thread2.start()

sender_thread1.start()
sender_thread2.start()
