import socket
import threading
import time
import queue

from src.OutboundPacket import OutboundPacket
from src.ThreadHandler import ThreadHandler
from src.packet import Packet
from src.SeqNumGenerator import SeqNumGenerator
from src.Transaction import Transaction

class PeerMiddleware:
    TIMEOUT_TIME = 1.0
    MAX_RETRIES = 4
    RECV_BYTES = 4096

    def __init__(self, my_id, my_port, peer_list, error_config):
        self.my_id = my_id
        self.peers = peer_list # Liste aus utils.load_peer_config
        self.error_config = error_config # Tuple: (target_msg_id, bit_index) oder None [cite: 61-63]
        
        # UDP Socket Setup [cite: 12, 32]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', my_port))
        self.sock.settimeout(PeerMiddleware.TIMEOUT_TIME)

        print(self.peers)

        for peer in self.peers:
            peer["seqNumber"] = SeqNumGenerator

        self.deliveryQueue = queue.Queue() # for messages received
        self.outboundPacketQueue = queue.Queue() # for messages to be sent
        self.preProcessingQueue = queue.Queue()
        self.transactionList = []

        self.reaper_sleep_time = 50
        self.running = True

        self.threadhandler = ThreadHandler(self)
        
        # Events für Stop-and-Wait Synchronisation


    def start(self):
        """
        Startet den Listener-Thread für eingehende Nachrichten.
        """
        self.threadhandler.startSenderThread()
        self.threadhandler.startReceiverThread()
        self.threadhandler.startReceiverThread()
        self.threadhandler.startPreProcessingThread()

    def message_prepare_thread(self):
        while self.running:
            packet = self.preProcessingQueue.get(timeout=PeerMiddleware.TIMEOUT_TIME)
            for peer in self.peers:
                self.outboundPacketQueue.put(OutboundPacket(packet, peer))
            self.preProcessingQueue.task_done()

    def sender_thread(self):
        while self.running:
            outboundPacket = self.outboundPacketQueue.get(timeout=PeerMiddleware.TIMEOUT_TIME)
            self.sock.sendto(outboundPacket.data.to_bytes(), outboundPacket.destination)
            transaction = Transaction(data=outboundPacket.data, timestamp=time.time(), retries=0, destination=outboundPacket.destination)
            self.transactionList.append(transaction)
            self.outboundPacketQueue.task_done()

    def receiver_thread(self):
        """
        Endlosschleife zum Empfangen von UDP-Paketen (Hintergrund-Thread).
        """
        while self.running:
            # TODO: Empfange Daten: data, addr = self.sock.recvfrom(buffer_size)[cite: 19].
            data, addr = self.sock.recvfrom(PeerMiddleware.RECV_BYTES)
            # --- Error Injection [cite: 18, 60] ---
            # TODO: Prüfe, ob Error Injection konfiguriert ist.

            # TODO: Parse vorläufig den Header, um Message-ID zu prüfen.
            # TODO: Falls Treffer: Flippe das Bit an 'bit_index' im 'data'-Bytearray mittels XOR (^). (I think not needed)
            packet = Packet().from_bytes(data)

            # --- Checksummen Prüfung [cite: 57, 65] ---
            # TODO: Berechne Checksumme über die empfangenen 'data'.
            # TODO: Wenn Checksumme != 0 (oder erwartet): Verwerfe Paket (continue).

            # process
            if packet.packetType == Packet.ACK_TYPE:
                for transaction in self.transactionList[:]:
                    if transaction.destination == addr and transaction.data.sequence_num == packet.sequence_num:
                        self.transactionList.remove(transaction)
                else:
                    continue
            else:
                self.preProcessingQueue.put(packet)


    def reaper_thread(self):
        while self.running:
            currentTime = time.time()
            for transaction in self.transactionList[:]:
                if (currentTime - transaction.timestamp) > PeerMiddleware.TIMEOUT_TIME:
                    self.transactionList.remove(transaction)
                    if transaction.retries + 1 < PeerMiddleware.MAX_RETRIES:
                        self.outboundPacketQueue.put(transaction.data)
            time.sleep(self.reaper_sleep_time)