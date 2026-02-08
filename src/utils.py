def load_peer_config(filepath):
    # Format: ID IP PORT
    # Example: 1 172.20.0.11 5001

    peers = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        peer_id = parts[0]
                        peer_ip = parts[1]
                        peer_port = int(parts[2])
                        peers[peer_id] = [peer_ip, peer_port]
                    except ValueError:
                        print(f"Warning: Invalid format in line: {line.strip()}")
    except FileNotFoundError:
        print(f"Error: Configuration file '{filepath}' not found.")
    
    return peers

import datetime

def log_message(filepath, sender_id, msg_type, msg_id, msg, payload):
    # Saves received messages to a file[cite: 43]
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [Peer {sender_id}] [Type {msg_type}] [Sqn-N {msg_id}] {msg}: {payload}\n"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to log file: {e}")