import socket
import threading
import time
import queue

from OutboundPacket import OutboundPacket
from ThreadHandler import ThreadHandler
from packet import Packet
from SeqNumGenerator import SeqNumGenerator
from Transaction import Transaction
import checksum as cs
from error_injection import inject_error
import utils as utils

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
        self.sock.bind(('', my_port))
        self.sock.settimeout(1.0)
        self.seqNumGenerator = SeqNumGenerator()
        self.deliveryQueue = queue.Queue() # for messages received
        self.outboundPacketQueue = queue.Queue() # for messages to be sent
        self.preProcessingQueue = queue.Queue()
        self.transactionList = []
        self.reaper_sleep_time = 0.5
        self.running = True
        self.injected_errors = set()
        self.received_seq_nums = {} # Dict: {sender_id: last_seq_num}
        
    def send_chat_message(self, text):
        """Called by TUI to send a message to all peers."""
        # Create packet object
        pkt = Packet()
        pkt.setSenderID(self.my_id)
        pkt.setSequenceNumber(self.seqNumGenerator.getSeqNum())
        pkt.setPayload(text)
        
        # Put into preProcessingQueue
        self.preProcessingQueue.put(pkt)

    def preProcessing_thread(self):
        while self.running:
            try:
                packet = self.preProcessingQueue.get(timeout=1.0)
                # Create One OutboundPacket per peer
                for peer_id, peer_info in self.peers.items():                    
                    target_ip, target_port = peer_info
                    # OutboundPacket needs (Packet, (ip, port))
                    self.outboundPacketQueue.put(OutboundPacket(packet, (target_ip, target_port)))
                    
                    time.sleep(1.0)
                self.preProcessingQueue.task_done()
            except queue.Empty:
                continue

    def sender_thread(self):
        while self.running:
            try:
                outboundPacket = self.outboundPacketQueue.get(timeout=1.0)
                
                # Convert packet to bytes (checksum calculated here)
                data_bytes = outboundPacket.data.to_bytes()
                
                self.sock.sendto(data_bytes, outboundPacket.destination)
                
                # Add to transaction list for reliability (ACK waiting)
                transaction = Transaction(
                    data=outboundPacket.data, 
                    timestamp=time.time(), 
                    retries=0, 
                    destination=outboundPacket.destination
                )
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
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break
            
            if self.error_config:
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
                        self.deliveryQueue.put(f"!!! {msg}") # Notify TUI
                        
                        data = inject_error(data, bit_idx)
                        self.injected_errors.add(seq_num_recv) # Mark as done

            # --- Checksum Validation ---
            if not cs.validate_checksum(data): 
                # Checksum failed
                msg = f"Checksum Mismatch! Dicarding packet from {addr}."
                # print(msg) 
                if self.log_file:
                    utils.log_message(self.log_file, "SYSTEM", "DROP", msg)
                self.deliveryQueue.put(f"!!! {msg}") # Notify TUI
                continue

            try:
                packet = Packet.from_bytes(data)
            except Exception as e:
                print(f"Error parsing packet: {e}")
                continue

            # process
            if packet.packetType == Packet.ACK_TYPE:
                # Remove from transaction list
                for transaction in self.transactionList[:]:
                    if transaction.destination == addr and transaction.data.sequence_number == packet.sequence_number:
                        self.transactionList.remove(transaction)
            else:
                # DATA Packet received
                
                # --- Duplicate Detection ---
                last_seq = self.received_seq_nums.get(packet.sender_id, -1)
                if packet.sequence_number <= last_seq:
                    # Duplicate!
                    msg = f"Duplicate Msg {packet.sequence_number} from Peer {packet.sender_id}. Dropping payload, re-sending ACK."
                    if self.log_file:
                        utils.log_message(self.log_file, "SYSTEM", "DUPLICATE", msg)
                    self.deliveryQueue.put(f"!!! {msg}")
                    
                    # Send ACK again (because the previous ACK might have been lost)
                    ack_pkt = Packet()
                    ack_pkt.setAck()
                    ack_pkt.setSenderID(self.my_id)
                    ack_pkt.setSequenceNumber(packet.sequence_number)
                    self.sock.sendto(ack_pkt.to_bytes(), addr)
                    continue # Stop processing (don't deliver)
                
                # New message - update state
                self.received_seq_nums[packet.sender_id] = packet.sequence_number
                
                # 1. Send ACK immediately
                ack_pkt = Packet()
                ack_pkt.setAck()
                ack_pkt.setSenderID(self.my_id)
                ack_pkt.setSequenceNumber(packet.sequence_number)
                # Checksum calc happens in to_bytes
                
                self.sock.sendto(ack_pkt.to_bytes(), addr)
                
                # 2. Deliver to Application (TUI)
                self.deliveryQueue.put(packet)

    def reaper_thread(self):
        while self.running:
            currentTime = time.time()
            for transaction in self.transactionList[:]:
                if (currentTime - transaction.timestamp) > PeerMiddleware.TIMEOUT_TIME:
                    if transaction.retries < PeerMiddleware.MAX_RETRIES:
                        # Retransmit
                        transaction.retries += 1
                        transaction.timestamp = currentTime # Reset timer
                        try:
                            self.sock.sendto(transaction.data.to_bytes(), transaction.destination)
                            msg = f"Timeout! Retransmitting Msg {transaction.data.sequence_number}..."
                            if self.log_file:
                                 utils.log_message(self.log_file, "SYSTEM", "RETRY", msg)
                            self.deliveryQueue.put(f"!!! {msg}")
                        except OSError as e:
                             print(f"Error retransmitting: {e}")
                    else:
                        self.transactionList.remove(transaction)
            time.sleep(self.reaper_sleep_time)