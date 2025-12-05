import socket
import threading
import time
from packet import Packet

class PeerMiddleware:
    def __init__(self, my_id, my_port, peer_list, error_config):
        self.my_id = my_id
        self.peers = peer_list # Liste aus utils.load_peer_config
        self.error_config = error_config # Tuple: (target_msg_id, bit_index) oder None [cite: 61-63]
        
        # UDP Socket Setup [cite: 12, 32]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', my_port))
        
        self.current_seq_num = 0
        self.running = True
        
        # Events für Stop-and-Wait Synchronisation
        self.ack_received_event = threading.Event()

    def start(self):
        """
        Startet den Listener-Thread für eingehende Nachrichten.
        """
        # TODO: Erstelle einen threading.Thread mit target=self._listen_loop.
        # TODO: Starte den Thread als Daemon.
        pass

    def send_multicast_message(self, text_payload):
        """
        Iterative Multicast Emulation[cite: 54].
        Wird vom UI (Main Thread) aufgerufen.
        """
        # TODO: Erhöhe self.current_seq_num für die neue Nachricht[cite: 30].
        # TODO: Erstelle das Packet-Objekt mit Payload und Header.
        # TODO: Berechne die Checksumme und setze sie im Paket.
        
        # Iteration über alle bekannten Peers (außer sich selbst, falls gewünscht, aber PDF sagt Closed Group [cite: 6])
        for peer in self.peers:
            # TODO: Rufe self._send_stop_and_wait(peer, packet) auf.
            
            # WICHTIG: Wartezeit zwischen den Peers einhalten [cite: 56]
            time.sleep(1.0) 

    def _send_stop_and_wait(self, peer, packet):
        """
        Stop-and-Wait ARQ Logik für einen einzelnen Peer[cite: 55].
        """
        attempt = 0
        max_retries = 3 [cite: 59]
        
        while attempt <= max_retries:
            # TODO: Sende das serialisierte Paket via self.sock.sendto an (peer_ip, peer_port).
            
            # TODO: Setze das Event zurück: self.ack_received_event.clear().
            
            # TODO: Warte auf ACK: if self.ack_received_event.wait(timeout=2.0):
            #    -> Wenn True (ACK kam): return (Erfolg).
            
            # TODO: Wenn Timeout abgelaufen:
            #    -> Erhöhe 'attempt'.
            #    -> Logge Retransmission.
        
        # TODO: Wenn Schleife endet ohne ACK -> Logge "Peer unreachable"[cite: 71].
        pass

    def _listen_loop(self):
        """
        Endlosschleife zum Empfangen von UDP-Paketen (Hintergrund-Thread).
        """
        while self.running:
            # TODO: Empfange Daten: data, addr = self.sock.recvfrom(buffer_size)[cite: 19].
            
            # --- Error Injection [cite: 18, 60] ---
            # TODO: Prüfe, ob Error Injection konfiguriert ist.
            # TODO: Parse vorläufig den Header, um Message-ID zu prüfen.
            # TODO: Falls Treffer: Flippe das Bit an 'bit_index' im 'data'-Bytearray mittels XOR (^).
            
            # --- Checksummen Prüfung [cite: 57, 65] ---
            # TODO: Berechne Checksumme über die empfangenen 'data'.
            # TODO: Wenn Checksumme != 0 (oder erwartet): Verwerfe Paket (continue).
            
            # --- Verarbeitung ---
            # TODO: Deserialisiere Paket (Packet.from_bytes).
            
            if packet.is_ack:
                # TODO: Prüfe, ob das ACK zur aktuell gesendeten Nachricht passt.
                # TODO: Setze self.ack_received_event.set() um den Sender-Thread zu wecken.
            else:
                # Es ist eine DATA Nachricht
                # TODO: Sende sofort ein ACK-Paket an 'addr' zurück.
                # TODO: Übergebe Payload an UI oder Log-Funktion[cite: 43].
                pass