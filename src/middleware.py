import socket
import time
import queue
from copy import deepcopy

from ThreadHandler import ThreadHandler
from packet import Packet
from SeqNumGenerator import SeqNumGenerator
from Transaction import Transaction
import checksum as cs
from error_injection import inject_error
import utils as utils
from PacketType import PacketType
from TransactionType import TransactionType
from DeliveryPacketType import DeliveryPacketType
from DeliveryPackets import DeliveryPacket


class PeerMiddleware:
    TIMEOUT_TIME = 1.0
    MAX_RETRIES = 3
    RECV_BYTES = 4096

    def __init__(self, my_id, my_port, peer_list, error_config):
        self.my_id = my_id
        self.peers = peer_list # Dict: {id: [ip, port]}
        self.error_config = error_config # Tuple: (target_msg_id, bit_index) oder None
        self.log_file = "messages.log"

        # UDP Socket Setup [cite: 12, 32]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', my_port))
        self.sock.settimeout(1.0)

        self.reversePeers = {}
        for peerID in self.peers:
            self.peers[peerID].append(SeqNumGenerator())
            self.reversePeers[self.peers[peerID][0] + str(self.peers[peerID][1])] = peerID

        print(self.reversePeers)
        self.deliveryQueue = queue.Queue() # for messages received
        self.outboundPacketQueue = queue.Queue() # for messages to be sent
        self.preProcessingQueue = queue.Queue()
        self.transactionList = []
        self.reaper_sleep_time = 0.5
        self.running = True
        self.injected_errors = None
        self.threadhandler = ThreadHandler(self)

    def start(self):
        self.threadhandler.startReceiverThread()
        self.threadhandler.startSenderThread()
        self.threadhandler.startReaperThread()
        self.threadhandler.startPreProcessingThread()

    def shutdown(self):
        self.threadhandler.shutdown()

    def send_chat_message(self, text):
        """Called by TUI to send a message to all peers."""
        # Create packet object
        pkt = Packet()
        pkt.setPayload(text)

        transaction = Transaction(packet=pkt, transactionType=TransactionType.DATA)
        # Put into preProcessingQueue
        self.preProcessingQueue.put(transaction)

    def preProcessing_thread(self):
        while self.running:
            try:
                transaction = self.preProcessingQueue.get(timeout=1.0)

                if transaction.transactionType == TransactionType.DATA:
                    transaction.packet.setSenderID(self.my_id)
                    # Create One packet per peer
                    for peerID in self.peers:
                        temp_transaction = deepcopy(transaction)
                        temp_transaction.destination = self.peers[peerID][0], self.peers[peerID][1]
                        temp_transaction.packet.setSequenceNumber(self.peers[peerID][2].getSeqNum())
                        self.outboundPacketQueue.put(temp_transaction)
                elif transaction.transactionType == TransactionType.ACK:
                    transaction.packet.setAck().setSenderID(self.my_id)
                    self.outboundPacketQueue.put(transaction)
                elif transaction.transactionType == TransactionType.RETRANSMIT:
                    transaction.retries += 1
                elif transaction.transactionType == TransactionType.RELAY:
                    packet = Packet().setSenderID(self.my_id).setPayload(transaction.packet.getPayload())
                    transaction_copy = Transaction(packet=packet, transactionType=TransactionType.DATA)
                    for peerID in self.peers:
                        if (self.peers[peerID][0], self.peers[peerID][1]) == transaction_copy.destination or self.my_id == peerID:
                            continue
                        temp_transaction = deepcopy(transaction_copy)
                        temp_transaction.destination = self.peers[peerID][0], self.peers[peerID][1]
                        temp_transaction.packet.setSequenceNumber(self.peers[peerID][2].getSeqNum())
                        self.outboundPacketQueue.put(temp_transaction)

                self.preProcessingQueue.task_done()

            except queue.Empty:
                continue

    def sender_thread(self):
        while self.running:
            try:
                transaction = self.outboundPacketQueue.get(timeout=1.0)

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

                self.outboundPacketQueue.task_done()
            except queue.Empty:
                continue

    def receiver_thread(self):
        """
        Receives UDP packets, validates checksums, handles error injection.
        """
        while self.running:
            try:
                data, addr = self.sock.recvfrom(PeerMiddleware.RECV_BYTES)
                utils.log_message(self.log_file, "SYSTEM", "RECEIVE",
                                  f"Received packet from addr {addr}")
            except socket.timeout:
                continue
            except OSError as e:
                print("An os error has occurred. Please restart the software.")
                print(e)
                break
            
            if self.error_config:
                inject_error(data)

            # --- Checksum Validation ---
            if not cs.validate_checksum(data):
                # Checksum failed
                msg = f"Checksum Mismatch! Discarding packet from {addr}."
                # print(msg) # Keeping console clean
                if self.log_file:
                    utils.log_message(self.log_file, "SYSTEM", "DROP", msg)
                self.deliveryQueue.put(DeliveryPacket(data=msg, type=DeliveryPacketType.SYSTEM_MESSAGE)) # Notify TUI
                continue

            try:
                packet = Packet.from_bytes(data)
            except Exception as e:
                print(f"Error parsing packet: {e}")
                continue

            utils.log_message(self.log_file, "SYSTEM", "RECEIVE",
                                  f"data {packet}")

            # process
            if packet.packetType == PacketType.ACK:
                # Remove from transaction list
                utils.log_message(self.log_file, "SYSTEM", "ACK", f"searching transaction {addr} and seq number {packet.getSequenceNumber()}")
                for transaction in self.transactionList[:]:
                    utils.log_message(self.log_file, "SYSTEM", "ACK",
                                      f"transaction {transaction.destination} and seq {transaction.packet.sequence_number}")
                    if transaction.destination == addr and transaction.packet.sequence_number == packet.getSequenceNumber():
                        self.transactionList.remove(transaction)
                        break
                else:
                    utils.log_message(self.log_file, "SYSTEM", "ACK",
                                      f"Got ACK that was not requested")
            else:
                # DATA Packet received

                # Prepare for ack send
                transaction = Transaction(packet=Packet().setAck().setSequenceNumber(packet.getSequenceNumber()), transactionType=TransactionType.ACK, destination=addr)
                self.preProcessingQueue.put(transaction)

                # 2. Deliver to Application (TUI)
                self.deliveryQueue.put(DeliveryPacket(data=packet, type=DeliveryPacketType.PACKET))
                
                # 3. Log it
                if self.log_file:
                    utils.log_message(self.log_file, packet.sender_id, packet.sequence_number, packet.payload)

    def reaper_thread(self):
        while self.running:
            currentTime = time.time()
            for transaction in self.transactionList[:]:
                if (currentTime - transaction.timestamp) > PeerMiddleware.TIMEOUT_TIME:
                    if transaction.retries < PeerMiddleware.MAX_RETRIES:
                        # Retransmit
                        self.preProcessingQueue.put(transaction)
                    else:
                        self.transactionList.remove(transaction)
            time.sleep(self.reaper_sleep_time)

    def inject_error(self, data):
        target_msg_id, bit_idx = self.error_config
        # Extract SeqNum (assuming standard header layout)
        if len(data) >= 5:
            seq_num_recv = int.from_bytes(data[1:5], byteorder='big')

            if seq_num_recv == target_msg_id and seq_num_recv not in self.injected_errors:
                # Identify Packet Type (Byte 0)
                pkt_type = "ACK" if data[0] == 0 else "Chat"
                msg = f"Simulating Bit-Flip on {pkt_type} Msg {seq_num_recv}..."
                if self.log_file:
                    utils.log_message(self.log_file, "SYSTEM", "ERR-INJECT", msg)
                self.deliveryQueue.put(DeliveryPacket(data=msg, type=DeliveryPacketType.SYSTEM_MESSAGE))  # Notify TUI

                data = inject_error(data, bit_idx)
                self.injected_errors.add(seq_num_recv)  # Mark as done
