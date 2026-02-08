import socket
import threading
import time
import queue
import checksum as cs
import utils as utils
import uuid

from copy import deepcopy
from ThreadHandler import ThreadHandler
from packet import Packet
from SeqNumGenerator import SeqNumGenerator
from Transaction import Transaction
from error_injection import inject_error
from PacketType import PacketType
from TransactionType import TransactionType
from DeliveryPacketType import DeliveryPacketType
from DeliveryPackets import DeliveryPacket
from Args import Args
from RelayPacketElement import RelayPacketElement
from SentPacketElement import SentPacketElement


class PeerMiddleware:
    TIMEOUT_TIME = 1.0
    ''' max three retries '''
    MAX_RETRIES = 3
    RECV_BYTES = 4096
    PROTECTION_MAX_TIME = 600 # 10 min
    WAIT_BETWEEN_SENDS = 1

    def __init__(self):
        self.args = Args()
        self.my_id = self.args.peerID
        self.peers = self.args.peers # Dict: {id: [ip, port]}
        self.log_file = self.args.log

        # UDP Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.args.port))
        self.sock.settimeout(1.0)

        self.seqNumGenerator = SeqNumGenerator()
        self.arqEvents = {}
        for peerID in self.peers:
            self.arqEvents[str(self.peers[peerID][0]) + str(self.peers[peerID][1])] = threading.Event

        self.deliveryQueue = queue.Queue() # for messages received
        self.outboundPacketQueue = queue.Queue() # for messages to be sent
        self.preProcessingQueue = queue.Queue()
        self.transactionList = []
        self.relayPacketList = []
        self.sentPacketList = []

        self.reaper_sleep_time = 0.5
        self.running = True

        self.injected_errors = set()
        self.injectionSetFlag = threading.Event()
        self.injectionSetFlag.clear()

        self.active_batches = {} # batch_id -> {total, success, fail}
        self.threadhandler = ThreadHandler(self)

    def start(self):
        self.threadhandler.startReceiverThread()
        self.threadhandler.startSenderThread()
        self.threadhandler.startReaperThread()
        self.threadhandler.startPreProcessingThread()

    def shutdown(self):
        self.threadhandler.shutdown()

    def setErrorInjectionConfig(self, config):
        self.injected_errors = config
        self.injectionSetFlag.set()

    def send_chat_message(self, text):
        # Create packet object
        pkt = Packet()
        pkt.setPayload(text)

        transaction = Transaction(packet=pkt, transactionType=TransactionType.DATA)
        transaction.batch_id = str(uuid.uuid4())
        # Put into preProcessingQueue
        self.preProcessingQueue.put(transaction)

    def preProcessing_thread(self):
        while self.running:
            try:
                transaction = self.preProcessingQueue.get(timeout=1.0)

                if transaction.transactionType == TransactionType.DATA:
                    transaction.packet.setSenderID(self.my_id).setSequenceNumber(self.seqNumGenerator.getSeqNum())

                    # Init batch tracking
                    if transaction.batch_id:
                        self.active_batches[transaction.batch_id] = {
                            'total': len(self.peers),
                            'success': 0,
                            'fail': 0
                        }

                    # Create one packet per peer
                    ''' Closed Group - send also to myself '''
                    for peerID in self.peers:
                        temp_transaction = deepcopy(transaction)
                        temp_transaction.batch_id = transaction.batch_id # bundle messages
                        temp_transaction.destination = self.peers[peerID][0], self.peers[peerID][1]
                        self.outboundPacketQueue.put(temp_transaction)

                elif transaction.transactionType == TransactionType.ACK:
                    transaction.packet.setAck().setSenderID(self.my_id)
                    self.outboundPacketQueue.put(transaction)

                elif transaction.transactionType == TransactionType.RETRANSMIT:
                    transaction.retries += 1
                    msg = f"Timeout! Retrying packet to {transaction.destination} (Attempt {transaction.retries}/{PeerMiddleware.MAX_RETRIES})"
                    utils.log_message(self.log_file, "SYSTEM", "RETRY", transaction.packet.getSequenceNumber(), msg, transaction)

                    # Queue for sending
                    self.outboundPacketQueue.put(transaction)

                elif transaction.transactionType == TransactionType.RELAY:
                    transaction_copy = Transaction(packet=transaction.packet, transactionType=TransactionType.DATA)
                    for peerID in self.peers:
                        if (self.peers[peerID][0], self.peers[peerID][1]) == transaction.destination or self.my_id == peerID:
                            continue
                        temp_transaction = deepcopy(transaction_copy)
                        temp_transaction.destination = self.peers[peerID][0], self.peers[peerID][1]
                        self.outboundPacketQueue.put(temp_transaction)

                self.preProcessingQueue.task_done()

            except queue.Empty:
                continue

    def sender_thread(self):
        while self.running:
            try:
                transaction = self.outboundPacketQueue.get(timeout=1.0)

                if not transaction.transactionType == TransactionType.ACK:
                    foundFlag = False
                    for action in self.transactionList[:]:
                        if action.destination == transaction.destination:
                            self.outboundPacketQueue.put(transaction)
                            foundFlag = True
                    if foundFlag:
                        continue

                if transaction.transactionType == TransactionType.DATA or transaction.transactionType == TransactionType.RELAY:
                    element = SentPacketElement(senderID=transaction.packet.getSenderID(),
                                                      sequenceNumber=transaction.packet.getSequenceNumber(),
                                                      counter=len(self.peers) - 1 if transaction.transactionType == TransactionType.DATA else len(self.peers) - 3, # -1, because the first will be sent rn if it is new. and relay does not self send and send to sender
                                                      timestamp=time.time())
                    existing_element = next((item for item in self.sentPacketList if item == element), None)
                    if existing_element:
                        if (time.time() - existing_element.timestamp) < PeerMiddleware.WAIT_BETWEEN_SENDS:
                            self.outboundPacketQueue.put(transaction)
                            continue
                        else:
                            existing_element.counter = existing_element.counter - 1
                            existing_element.timestamp = time.time()
                            if existing_element.counter == 0:
                                self.sentPacketList.remove(existing_element)
                    else:
                        self.sentPacketList.append(element)

                # Convert packet to bytes (checksum calculated here)
                data_bytes = transaction.packet.to_bytes()

                self.sock.sendto(data_bytes, transaction.destination)

                if transaction.transactionType == TransactionType.DATA:
                    transaction.timestamp = time.time()
                    transaction.retries = 0
                    self.transactionList.append(transaction)
                elif transaction.transactionType == TransactionType.RETRANSMIT:
                    transaction.timestamp = time.time()
                    self.transactionList.append(transaction)

                utils.log_message(self.log_file, "SYSTEM", "SEND", transaction.packet.getSequenceNumber(),
                                  f"Sending {transaction.transactionType} packet to {transaction.destination}", transaction)

                self.outboundPacketQueue.task_done()
            except queue.Empty:
                continue

    def receiver_thread(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(PeerMiddleware.RECV_BYTES)
            except socket.timeout:
                continue
            except OSError as e:
                print("An os error has occurred. Please restart the software.")
                print(e)
                break

            if self.injectionSetFlag.is_set():
                data = self.checkIfInjectionPacket(data)

            # Checksum Validation
            if not cs.validate_checksum(data):
                # Checksum failed
                msg = f"Checksum Mismatch! Discarding packet from {addr}."
                # print(msg)
                if self.log_file:
                    utils.log_message(self.log_file, "SYSTEM", "DROP", "UNKNOWN", msg, data)
                self.deliveryQueue.put(DeliveryPacket(data=msg, type=DeliveryPacketType.SYSTEM_MESSAGE)) # Notify TUI
                continue

            try:
                packet = Packet.from_bytes(data)
            except Exception as e:
                print(f"Error parsing packet: {e}")
                continue

            # process
            if packet.packetType == PacketType.ACK:
                # Remove from transaction list
                for transaction in self.transactionList[:]:
                    if transaction.destination == addr and transaction.packet.sequence_number == packet.getSequenceNumber():

                        # Batch Success
                        if transaction.batch_id and transaction.batch_id in self.active_batches:
                             self.active_batches[transaction.batch_id]['success'] += 1
                             self.check_batch_complete(transaction.batch_id)

                        self.transactionList.remove(transaction)
                        break
            else:
                # DATA Packet received
                relayElement = RelayPacketElement(senderID=packet.getSenderID(), sequenceNumber=packet.getSequenceNumber(), timestamp=time.time())
                if not relayElement in self.relayPacketList:
                    self.relayPacketList.append(relayElement)

                    transaction = Transaction(packet=packet, transactionType=TransactionType.RELAY, destination=addr)
                    self.preProcessingQueue.put(transaction)

                    # Deliver to Application
                    self.deliveryQueue.put(DeliveryPacket(data=packet, type=DeliveryPacketType.PACKET))

                # Prepare for ack send
                transaction = Transaction(packet=Packet().setAck().setSequenceNumber(packet.getSequenceNumber()), transactionType=TransactionType.ACK, destination=addr)
                self.preProcessingQueue.put(transaction)

            utils.log_message(self.log_file, packet.getSenderID(), "RECEIVE", packet.getSequenceNumber(),
                              f"Received packet from addr {addr}", packet)

    def reaper_thread(self):
        while self.running:
            currentTime = time.time()
            for transaction in self.transactionList[:]:
                if (currentTime - transaction.timestamp) > PeerMiddleware.TIMEOUT_TIME:
                    ''' Validity - Stop-and-Wait ARQ'''
                    if transaction.retries < PeerMiddleware.MAX_RETRIES:
                        # Retransmit
                        transaction.transactionType = TransactionType.RETRANSMIT
                        self.preProcessingQueue.put(transaction)
                    else:
                        # Max retries reached
                        msg = f"Message to {transaction.destination} failed after {PeerMiddleware.MAX_RETRIES} attempts."
                        utils.log_message(self.log_file, "SYSTEM", "DROP", transaction.packet.getSequenceNumber(), msg, transaction)

                        # Batch Fail
                        if transaction.batch_id and transaction.batch_id in self.active_batches:
                             self.active_batches[transaction.batch_id]['fail'] += 1
                             self.check_batch_complete(transaction.batch_id)

                    self.transactionList.remove(transaction)

            for element in self.relayPacketList[:]:
                if (currentTime - element.timestamp) > PeerMiddleware.PROTECTION_MAX_TIME:
                    self.relayPacketList.remove(element)

            time.sleep(self.reaper_sleep_time)

    def check_batch_complete(self, batch_id):
        if batch_id not in self.active_batches:
            return

        batch = self.active_batches[batch_id]
        if batch['success'] + batch['fail'] == batch['total']:
             msg = f"[Status] {batch['success']}/{batch['total']} ACKs received"
             self.deliveryQueue.put(DeliveryPacket(data=msg, type=DeliveryPacketType.SYSTEM_MESSAGE))
             del self.active_batches[batch_id]

    def checkIfInjectionPacket(self, data):
        target_msg_id, bit_idx = self.injected_errors
        packet = Packet.from_bytes(data)
        msg = f"sanity check {str(packet.getSenderID()) + str(packet.getSequenceNumber())}  {target_msg_id}"
        utils.log_message(self.log_file, "SYSTEM", "ERR-INJECT", packet.getSequenceNumber(), msg, packet)
        if str(packet.getSenderID()) + str(packet.getSequenceNumber()) == target_msg_id:
            # Identify Packet Type (Byte 0)
            msg = f"Simulating Bit-Flip on packet with message ID {target_msg_id} at bit {bit_idx}"
            utils.log_message(self.log_file, "SYSTEM", "ERR-INJECT", packet.getSequenceNumber(), msg, packet)
            self.deliveryQueue.put(DeliveryPacket(data=msg, type=DeliveryPacketType.SYSTEM_MESSAGE))  # Notify TUI

            self.injectionSetFlag.clear()
            return inject_error(data, bit_idx)
        return data