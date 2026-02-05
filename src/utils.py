def load_peer_config(filepath):
    """
    Format: ID IP PORT
    Example: 1 127.0.0.1 5001
    """
    peers = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        peer_id = int(parts[0])
                        peer_ip = parts[1]
                        peer_port = int(parts[2])
                        peers[peer_id] = [peer_ip, peer_port]
                    except ValueError:
                        print(f"Warning: Invalid format in line: {line.strip()}")
    except FileNotFoundError:
        print(f"Error: Configuration file '{filepath}' not found.")
    
    return peers

def log_message(filepath, sender_id, msg_id, payload):
    """
    Saves received messages to a file[cite: 43].
    """
    # TODO: Open log file in append mode ('a').
    # TODO: Write timestamp, sender ID, message ID, and text payload.
    # TODO: Flush or close the file to prevent data loss.
    pass