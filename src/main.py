import argparse
import sys

from middleware import PeerMiddleware
from ThreadHandler import ThreadHandler
from tui import PeerTUI  # Importiere deine neue TUI-Klasse
from utils import load_peer_config


def print_banner():
    print(r"""
  ____  ____  ____     ____  _           _
 |  _ \|___ \|  _ \   / ___|| |__   __ _| |_
 | |_) | __) | |_) | | |    | '_ \ / _` | __|
 |  __/ / __/|  __/  | |___ | | | | (_| | |_
 |_|   |_____|_|      \____||_| |_|\__,_|\__|
    """)
    print("Distributed Systems Dependability - Fernlehre")
    print("-" * 50)


def main():
    # 1. Argument Parsing (Bleibt in main.py)
    parser = argparse.ArgumentParser(description="P2P Chat with Error Injection")
    parser.add_argument("--id", type=int, required=False, help="Peer ID")
    parser.add_argument("--port", type=int, required=False, help="Own Port")
    parser.add_argument("--peers", type=str, required=False, help="Path to config file")
    parser.add_argument("--log", type=str, required=False, help="Path to log file")
    parser.add_argument(
        "--error_msg_id", type=int, default=None, help="ID for error injection"
    )
    parser.add_argument(
        "--error_bit_idx", type=int, default=None, help="Bit index for error"
    )

    args = parser.parse_args()
    print_banner()

    mw = None
    handler = None

    # 2. Initialisierung der Middleware
    if args.id and args.port and args.peers and args.log:
        peers = load_peer_config(args.peers)
        error_config = (
            (args.error_msg_id, args.error_bit_idx)
            if args.error_msg_id is not None
            else None
        )

        try:
            # Middleware-Instanz erstellen
            mw = PeerMiddleware(args.id, args.port, peers, error_config)

            # Hintergrund-Threads über den ThreadHandler starten
            handler = ThreadHandler(mw)
            handler.startReceiverThread()
            handler.startSenderThread()
            handler.startReaperThread()
            # Falls vorhanden: handler.startPreProcessingThread()

            print(f"Middleware for Peer {args.id} initialized and threads started.")
        except Exception as e:
            print(f"Failed to initialize Middleware: {e}")
            sys.exit(1)
    else:
        print(
            "Configuration missing. Please start with all required arguments or use 'setup' in TUI."
        )

    # 3. Start der TUI (Ersetzt die alte while-Schleife)
    try:
        # Wir übergeben das Middleware-Objekt an die TUI
        tui = PeerTUI(mw, args)
        tui.cmdloop()  # Startet die interaktive Shell
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # 4. Cleanup
        if handler:
            print("Shutting down threads...")
            handler.shutdown()
        print("Cleanup done.")


if __name__ == "__main__":
    main()
