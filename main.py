import sys
import argparse
from utils import load_peer_config, log_message

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
    # Argument Parsing
    parser = argparse.ArgumentParser(description="P2P Chat with Error Injection")
    
    parser.add_argument("--id", type=int, required=False, help="Peer ID")
    parser.add_argument("--port", type=int, required=False, help="Own Port")
    parser.add_argument("--peers", type=str, required=False, help="Path to config file")
    parser.add_argument("--log", type=str, required=False, help="Path to log file")
    parser.add_argument("--error_msg_id", type=int, default=None, help="Optional: ID for error injection")
    parser.add_argument("--error_bit_idx", type=int, default=None, help="Optional: Bit index for error")
    
    args = parser.parse_args()

    # Setup
    print_banner()
    
    peers = []
    mw = None
    
    # enough arguments to auto-start
    if args.id and args.port and args.peers and args.log:
        print(f"Peer ID: {args.id}")
        print(f"Port: {args.port}")
        if args.error_msg_id is not None:
            print(f"Error Injection: MsgID={args.error_msg_id}, BitIdx={args.error_bit_idx}")
        else:
            print("Error Injection: Disabled")
        
        peers = load_peer_config(args.peers)
        print(f"Loaded {len(peers)} peers from {args.peers}")
        
        try:
            mw = PeerMiddleware(args.id, args.port, peers, (args.error_msg_id, args.error_bit_idx))
            # mw.start()
            print("Middleware initialized.")
        except Exception as e:
            print(f"Failed to initialize Middleware: {e}")
            mw = None
    else:
        print("Configuration missing. Use 'setup' command to configure.")

    print("-" * 50)
    print("Commands: help, status, setup, exit, <message>")

    # UI
    try:
        while True:
            current_id = args.id if args.id else "?"
            try:
                user_input = input(f"\nPeer {current_id} >> ")
            except EOFError:
                break
            
            cmd = user_input.strip().lower()
            
            if cmd == "exit":
                break
            elif cmd == "help":
                print("Available commands:")
                print("  help           - Show this help")
                print("  setup          - Configure peer interactively")
                print("  status         - Show current status and peers")
                print("  exit    - Exit the application")
                print("  <message>      - Send a message to all peers")
            
            elif cmd == "setup":
                try:
                    p_id = input("Enter Peer ID: ").strip()
                    p_port = input("Enter Port: ").strip()
                    p_peers = input("Enter Peers Config Path: ").strip()
                    p_log = input("Enter Log File Path (default: logs.log): ").strip()
                    if not p_log:
                        p_log = "logs.log"
                    
                    if not (p_id and p_port and p_peers):
                        print("ID, Port and Peers Config are required.")
                        continue
                        
                    args.id = int(p_id)
                    args.port = int(p_port)
                    args.peers = p_peers
                    args.log = p_log
                    
                    peers = load_peer_config(args.peers)
                    print(f"Loaded {len(peers)} peers.")
                    
                    if mw:
                        mw.stop()
                    
                    mw = PeerMiddleware(args.id, args.port, peers, None)
                    # mw.start()
                    print("Middleware initialized.")
                    
                except ValueError:
                    print("Invalid input (ID/Port must be integers).")
                except Exception as e:
                    print(f"Setup failed: {e}")

            elif cmd == "status":
                print(f"ID={args.id}, Port={args.port}")
                print(f"Peers: {len(peers)}")
                for p in peers:
                    print(f"  - ID: {p['id']}, IP: {p['ip']}, Port: {p['port']}")
            elif cmd == "":
                continue
            else:
                # message
                if mw:
                    print(f"Sending message to {len(peers)} peers: {user_input}")
                    try:
                        mw.send_multicast_message(user_input)
                    except Exception as e:
                        print(f"Error sending message: {e}")
                else:
                    print("Middleware not running. Run setup first.")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if mw:
            mw.stop()
        print("Cleanup done.")

if __name__ == "__main__":
    main()