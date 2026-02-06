import blessed
import time
from queue import Empty

from middleware import PeerMiddleware
from ThreadHandler import ThreadHandler
import utils
from DeliveryPacketType import DeliveryPacketType

# Constants for layout
INPUT_HEIGHT = 3

class PeerTUI:
    def __init__(self, middleware, args, handler=None):
        self.mw = middleware
        self.handler = handler
        self.args = args
        self.configured = middleware is not None
        
        self.term = blessed.Terminal()
        self.running = True
        
        # Chat history buffer
        self.history = []
        self.max_history = 100
        
        # User input buffer
        self.input_buffer = []
        self.cursor_pos = 0
        
        # Prompt
        if self.configured and args:
             self.prompt = f"(Peer {args.id}) >> "
        else:
             self.prompt = "(Unconfigured) >> "

    def run(self):
        """Main loop for the TUI."""
        try:
            print(self.term.enter_fullscreen())
            print(self.term.clear())
            
            # Initial Welcome Message
            self.add_system_message(r"  ____  _____  _____ ")
            self.add_system_message(r" |  _ \|  ___||_   _|")
            self.add_system_message(r" | |_) | |___  |  |  ")
            self.add_system_message(r" |  __/| |___  |  |  ")
            self.add_system_message(r" |_|   |_____| |__|  ")
            self.add_system_message("") # Explicit blank line
            
            if not self.configured:
                 self.add_system_message("System UNCONFIGURED.")
                 self.add_system_message("Please run /setup to configure Peer ID and Port.")
            else:
                 self.add_system_message("System Ready.")

            # Draw initial layout
            self.draw_layout()
            
            with self.term.cbreak(), self.term.hidden_cursor():
                while self.running:
                    # Check middleware running state if configured
                    if self.configured and self.mw and not self.mw.running:
                        self.running = False
                        break
                    # 1. Check for User Input (Non-blocking check)
                    val = self.term.inkey(timeout=0.05) # Reduced timeout for snappier feel
                    if val:
                        self.handle_input(val)
                        self.draw_input_area()
                    
                    # 2. Check for Incoming Messages from Middleware
                    if self.configured and self.check_incoming_messages():
                        self.draw_history()
                        self.draw_input_area()
        finally:
            print(self.term.exit_fullscreen())
            print(self.term.clear())

    def draw_layout(self):
        """Redraws the entire screen."""
        print(self.term.clear())
        
        # Header
        with self.term.location(0, 0):
            if self.configured:
                header = f" Distributed Systems Dependability - Peer {self.args.id} "
            else:
                header = " Distributed Systems Dependability - UNCONFIGURED "
            print(header.center(self.term.width, "="))
            
        # Draw History
        self.draw_history()
        
        # Draw Divider
        divider_y = self.term.height - INPUT_HEIGHT - 1
        with self.term.location(0, divider_y):
            print("-" * self.term.width)
            
        # Help Bar below divider
        with self.term.location(0, divider_y + 1):
             print(" [/setup] Setup | [/help] Help | [/status] Infos | [/quit] Exit")

        self.draw_input_area()

    def draw_history(self):
        """Draws the chat history in the top section."""
        history_height = self.term.height - INPUT_HEIGHT - 3 # Adjusted for help bar
        
        # Get the last N messages that fit
        msgs_to_show = self.history[-history_height:]
        
        with self.term.location(0, 1):
            for i, msg in enumerate(msgs_to_show):
                print(self.term.clear_eol + msg)

    def draw_input_area(self):
        """Draws the input area at the bottom."""
        input_y = self.term.height - 1
        with self.term.location(0, input_y):
            print(self.term.clear_eol + self.prompt + "".join(self.input_buffer), end="", flush=True)
            
            # Draw fake cursor
            cursor_x = len(self.prompt) + self.cursor_pos
            print(self.term.move_xy(cursor_x, input_y) + "_", end="", flush=True)

    def handle_input(self, val):
        """Handles a single keypress."""
        if val.is_sequence:
            if val.name == "KEY_ENTER":
                self.submit_message()
            elif val.name == "KEY_BACKSPACE":
                if self.input_buffer and self.cursor_pos > 0:
                    self.input_buffer.pop(self.cursor_pos - 1)
                    self.cursor_pos -= 1
            elif val.name == "KEY_LEFT":
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif val.name == "KEY_RIGHT":
                if self.cursor_pos < len(self.input_buffer):
                    self.cursor_pos += 1
            elif val.name == "KEY_ESCAPE":
                self.running = False
        else:
            self.input_buffer.insert(self.cursor_pos, str(val))
            self.cursor_pos += 1
            
        self.draw_input_area()

    def submit_message(self):
        msg = "".join(self.input_buffer)
        self.input_buffer = []
        self.cursor_pos = 0
        
        if not msg.strip():
            return
            
        if msg == "/exit" or msg == "/quit":
            self.running = False
            return
        
        if msg == "/setup":
            if self.configured:
                self.add_system_message("Already configured!")
            else:
                self.command_setup()
            return

        if msg == "/help":
            self.add_system_message("Available Commands:")
            self.add_system_message("  /status - Show current peer status")
            self.add_system_message("  /quit   - Exit the application")
            if not self.configured:
                self.add_system_message("  /setup  - Configure the peer")
            self.add_system_message("  /help   - Show this help message")
            return
            
        if not self.configured:
            self.add_system_message("System unconfigured. Run /setup first.")
            return
        
        if msg == "/status":
            self.add_system_message(f"Status: MyID={self.args.id}, Port={self.args.port}, Peers={len(self.mw.peers)}")
            return

        if hasattr(self.mw, 'send_chat_message'):
             self.mw.send_chat_message(msg)

        else:
             self.add_system_message(f"Sending: {msg}")
             try:
                 self.mw.send_chat_message(msg)
             except AttributeError:
                 self.add_system_message("Error: Middleware.send_chat_message not implemented yet.")

    def check_incoming_messages(self):
        """Checks the middleware's delivery queue for new messages."""
        if not self.configured or not self.mw:
             return False

        received = False
        try:
            while True:
                deliveryPacket = self.mw.deliveryQueue.get_nowait()
                
                # Format message
                timestamp = time.strftime("%H:%M:%S")
                # Assuming packet is a Packet object or a tuple with sender info
                if deliveryPacket.type == DeliveryPacketType.PACKET:
                    packet = deliveryPacket.data
                    display_msg = f"[{timestamp}] [Peer {packet.sender_id}] {packet.payload}"
                    
                    # LOGGING (Requirement: UI saves payload to file)
                    if hasattr(self.args, 'log') and self.args.log:
                        # We need to import utils if not present, but it is imported at top
                        try:
                            utils.log_message(self.args.log, packet.sender_id, packet.sequence_number, packet.payload)
                        except Exception as e:
                            self.add_system_message(f"Log Error: {e}")

                elif deliveryPacket.type == DeliveryPacketType.SYSTEM_MESSAGE:
                    self.add_system_message(deliveryPacket.data)

                else:
                    display_msg = f"[{timestamp}] {packet}" # Fallback
                
                self.add_to_history(display_msg)
                received = True
                
        except Empty:
            pass
        return received

    def add_to_history(self, line):
        self.history.append(line)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.draw_history()
        # Also redraw input to ensure cursor stays on top
        self.draw_input_area()

    def add_system_message(self, text):
        self.add_to_history(self.term.yellow(text))

    def read_line(self, prompt_text):
        """Reads a line of input while in cbreak mode."""
        buffer = []
        
        # Helper inner function to draw the wizard input line
        def draw_wizard_input():
            input_y = self.term.height - 1
            with self.term.location(0, input_y):
                print(self.term.clear_eol + prompt_text + "".join(buffer), end="", flush=True)
                # Cursor
                cursor_x = len(prompt_text) + len(buffer)
                print(self.term.move_xy(cursor_x, input_y) + "_", end="", flush=True)

        draw_wizard_input()
        
        while True:
            val = self.term.inkey()
            if val.name == "KEY_ENTER":
                return "".join(buffer)
            elif val.name == "KEY_BACKSPACE":
                if buffer:
                    buffer.pop()
                    draw_wizard_input()
            elif val.is_sequence:
                pass 
            else:
                buffer.append(str(val))
                draw_wizard_input()

    def command_setup(self):
        """Interactive setup wizard."""
        try:
             self.add_system_message("--- SETUP WIZARD ---")
             
             # 1. Peer ID
             while True:
                 str_id = self.read_line("Enter Peer ID (int): ")
                 if str_id.isdigit():
                     peer_id = int(str_id)
                     break
                 self.add_system_message("Invalid ID. Please enter a number.")
             
             # 2. Port
             while True:
                 str_port = self.read_line("Enter Port (int): ")
                 if str_port.isdigit():
                     port = int(str_port)
                     break
                 self.add_system_message("Invalid Port. Please enter a number.")
             
             # 3. Peers File
             while True:
                 peers_file = self.read_line("Enter Peers File [peers.txt]: ")
                 if not peers_file.strip():
                     peers_file = "peers.txt"
                 # Verify?
                 try:
                     peers = load_peer_config(peers_file)
                     break
                 except Exception as e:
                     self.add_system_message(f"Error loading file: {e}")
             
             # 4. Initialize
             self.add_system_message("Initializing Middleware...")
             
             # Mock Args if needed or update self.args
             # We create a simple object to hold args
             class Args:
                 pass
             new_args = Args()
             new_args.id = peer_id
             new_args.port = port
             new_args.peers = peers_file
             new_args.log = f"peer{peer_id}.log" # Auto-gen log name
             new_args.error_msg_id = None
             new_args.error_bit_idx = None
             
             self.args = new_args
             
             # Init Middleware
             mw = PeerMiddleware(peer_id, port, peers, None)
             mw.log_file = new_args.log
             
             # Init Handler
             handler = ThreadHandler(mw)
             handler.startReceiverThread()
             handler.startSenderThread()
             handler.startReaperThread()
             handler.startPreProcessingThread()
             
             self.mw = mw
             self.configured = True
             self.prompt = f"(Peer {peer_id}) >> "
             
             self.add_system_message("Setup Complete! System is now running.")
             self.add_system_message(f"Logging to {new_args.log}")
             
        except Exception as e:
            self.add_system_message(f"Setup Failed: {e}")
            import traceback
            traceback.print_exc()
