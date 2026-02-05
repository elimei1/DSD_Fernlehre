import cmd


class PeerTUI(cmd.Cmd):
    # console design
    intro = "=== P2P Reliable Chat System ===\nType help or ? to list commands."
    prompt = ">> "

    def __init__(self, middleware, args):
        super().__init__()
        self.mw = middleware
        self.args = args
        self.prompt = f"(Peer {args.id if args.id else '?'}) >> "

    def do_status(self, arg):
        """Show current peer status and configured peers."""
        # Access to middleware data
        print(f"My ID: {self.mw.my_id}")
        print(f"Peers in group: {len(self.mw.peers)}")
        for p_id, info in self.mw.peers.items():
            print(f" - Peer {p_id}: {info[0]}:{info[1]}")

    def do_setup(self, arg):
        """Re-configure the peer settings interactively."""
        # Implementiere hier die interaktive Konfiguration
        print("Starting interactive setup...")
        # (Logik analog zu deinem bisherigen main.py setup)

    def default(self, line):
        """Any input that is not a command is sent as a message payload."""
        if not line:
            return
        if self.mw:
            print(f"Sending message: {line}")
            # Hier rufst du deine Multicast-Logik auf
            # self.mw.send_multicast_message(line)
        else:
            print("Error: Middleware not running.")

    def do_exit(self, arg):
        """Close the application and stop all threads."""
        print("Exiting...")
        return True  # Beendet die cmdloop
