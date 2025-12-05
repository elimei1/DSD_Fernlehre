import sys
import argparse
from middleware import PeerMiddleware
from utils import load_peer_config, log_message

def main():
    # --- Argument Parsing [cite: 46-52] ---
    parser = argparse.ArgumentParser(description="P2P Chat mit Error Injection")
    # TODO: Füge Argumente hinzu:
    # --id (Peer ID)
    # --port (Eigener Port)
    # --peers (Pfad zur Config-Datei)
    # --log (Pfad zur Log-Datei)
    # --error_msg_id (Optional: ID für Fehler-Injection)
    # --error_bit_idx (Optional: Bit Index für Fehler)
    
    args = parser.parse_args()

    # --- Setup ---
    # TODO: Lade Peer-Liste: peers = load_peer_config(args.peers)
    
    # TODO: Initialisiere Middleware: 
    # mw = PeerMiddleware(args.id, args.port, peers, (args.error_msg_id, args.error_bit_idx))
    
    # TODO: Starte Middleware Thread: mw.start()

    print(f"Peer {args.id} gestartet auf Port {args.port}. 'exit' zum Beenden.")

    # --- UI Loop [cite: 40, 42] ---
    try:
        while True:
            # TODO: Warte auf Benutzereingabe: user_input = input("Nachricht: ")
            
            if user_input.strip() == "exit":
                break
                
            # TODO: Übergib Nachricht an Middleware: mw.send_multicast_message(user_input)
            
    except KeyboardInterrupt:
        print("Beende...")
    finally:
        # TODO: Aufräumarbeiten (Socket schließen etc.)
        pass

if __name__ == "__main__":
    main()