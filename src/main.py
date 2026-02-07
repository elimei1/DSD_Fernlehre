import argparse
import sys
from middleware import PeerMiddleware
from tui import PeerTUI
from utils import load_peer_config


def main():
    # Argument Parsing
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

    mw = None
    handler = None

    # Init Middleware
    if args.id and args.port and args.peers and args.log:
        peers = load_peer_config(args.peers)
        error_config = (
            (args.error_msg_id, args.error_bit_idx)
            if args.error_msg_id is not None else None
        )

        try:
            mw = PeerMiddleware(args.id, args.port, peers, error_config)
            mw.log_file = args.log
            mw.start()

            print(f"Middleware for Peer {args.id} initialized and threads started.")
        except Exception as e:
            print(f"Failed to initialize Middleware: {e}")
            sys.exit(1)
    else:
        print("UNCONFIGURED mode. Please run /setup")
        mw = None
        handler = None

    # Start tui
    try:
        tui = PeerTUI(mw, args)
        tui.run()
    except KeyboardInterrupt:
        print("\nExiting (KeyboardInterrupt)")
    except Exception as e:
        import traceback
        print("\nCRITICAL ERROR in TUI:")
        traceback.print_exc()
    finally:
        # Cleanup
        active_handler = tui.handler if 'tui' in locals() and tui and tui.handler else handler
        
        if active_handler:
            print("Shutting down threads")
            active_handler.shutdown()
        print("Cleanup done")


if __name__ == "__main__":
    main()
