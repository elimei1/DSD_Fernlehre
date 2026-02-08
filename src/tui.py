import blessed
import time
import utils

from queue import Empty
from middleware import PeerMiddleware
from DeliveryPacketType import DeliveryPacketType
from Args import Args

INPUT_HEIGHT = 3

''' Terminal UI '''
''' Text only english '''
class PeerTUI:
    def __init__(self, middleware, args, handler=None):
        self.mw = middleware
        self.handler = handler
        self.args = Args()
        self.configured = middleware is not None
        self.term = blessed.Terminal()
        self.running = True
        self.history = []
        self.max_history = 100
        self.input_buffer = []
        self.cursor_pos = 0
        
        # Prompt
        if self.configured and self.args:
             self.prompt = f"(Peer {self.args.peerID}) >> "
        else:
             self.prompt = "(Unconfigured) >> "

    def run(self):
        # Main loop
        try:
            print(self.term.enter_fullscreen())
            print(self.term.clear())
            
            # Welcome Message
            self.add_system_message(r"  ____  _____  _____ ")
            self.add_system_message(r" |  _ \|  ___||_   _|")
            self.add_system_message(r" | |_) | |___  |  |  ")
            self.add_system_message(r" |  __/| |___  |  |  ")
            self.add_system_message(r" |_|   |_____| |__|  ")
            self.add_system_message("")
            
            if not self.configured:
                 self.add_system_message("System UNCONFIGURED.")
                 self.add_system_message("Please run /setup")
            else:
                 self.add_system_message("System Ready.")

            # Draw initial layout
            self.draw_layout()
            with self.term.cbreak(), self.term.hidden_cursor():
                while self.running:
                    # Check middleware
                    if self.configured and self.mw and not self.mw.running:
                        self.running = False
                        break
                    # Check User Input
                    val = self.term.inkey(timeout=0.05)
                    if val:
                        self.handle_input(val)
                        self.draw_input_area()
                    
                    # Check Incoming Messages
                    if self.configured and self.check_incoming_messages():
                        self.draw_history()
                        self.draw_input_area()
        finally:
            print(self.term.exit_fullscreen())
            print(self.term.clear())

    def draw_layout(self):
        # Redraws entire screen
        print(self.term.clear())
        
        # Header
        with self.term.location(0, 0):
            if self.configured:
                header = f" PET - Peer {self.args.peerID} "
            else:
                header = " PET - UNCONFIGURED "
            print(header.center(self.term.width, "="))
            
        # Draw History
        self.draw_history()
        
        # Draw Divider
        divider_y = self.term.height - INPUT_HEIGHT - 1
        with self.term.location(0, divider_y):
            print("-" * self.term.width)
            
        # Help Bar
        with self.term.location(0, divider_y + 1):
             print(" [/setup] Setup | [/error] Error | [/help] Help | [/status] Infos | [/quit] Exit")

        self.draw_input_area()

    def draw_history(self):
        history_height = self.term.height - INPUT_HEIGHT - 3
        
        # Messages that fit on screen
        msgs_to_show = self.history[-history_height:]
        with self.term.location(0, 1):
            for i, msg in enumerate(msgs_to_show):
                print(self.term.clear_eol + msg)

    def draw_input_area(self):
        input_y = self.term.height - 1
        with self.term.location(0, input_y):
            print(self.term.clear_eol + self.prompt + "".join(self.input_buffer), end="", flush=True)
            
            cursor_x = len(self.prompt) + self.cursor_pos
            print(self.term.move_xy(cursor_x, input_y) + "_", end="", flush=True)

    ''' Handle user input with arbitrary payload'''
    def handle_input(self, val):
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
            self.add_system_message("  /error  - Inject an error")
            if not self.configured:
                self.add_system_message("  /setup  - Configure the peer")
            self.add_system_message("  /help   - Show this help message")
            return
            
        if msg.startswith("/error"):
            parts = msg.split()
            if len(parts) == 1:
                # Default 2 2
                ''' Error Injection on message ID and bit index '''
                self.mw.setErrorInjectionConfig(("peer_12", 2))
                self.add_system_message("Error injection set to peerID=peer_1, MSG_ID=2, BIT_IDX=2")
            elif len(parts) == 3:
                try:
                    msg_id = parts[1]
                    bit_idx = int(parts[2])
                    self.mw.setErrorInjectionConfig((msg_id, bit_idx))
                    self.add_system_message(f"Error injection set to MSG_ID={msg_id}, BIT_IDX={bit_idx}")
                except ValueError:
                    self.add_system_message("Invalid arguments. Usage: /error [msg_id] [bit_idx]")
            else:
                 self.add_system_message("Invalid usage. Usage: /error [msg_id] [bit_idx] or just /error")
            return
            
        if not self.configured:
            self.add_system_message("System unconfigured. Run /setup first.")
            return
        
        if msg == "/status":
            err_conf = self.mw.injected_errors if self.mw.injectionSetFlag.is_set() else "None"
            self.add_system_message(f"Status: MyID={self.args.peerID}, Port={self.args.port}, Peers={len(self.mw.peers)}, ErrorConfig={err_conf}")
            return

        self.mw.send_chat_message(msg)

    def check_incoming_messages(self):
        if not self.configured or not self.mw:
             return False

        received = False
        try:
            while True:
                deliveryPacket = self.mw.deliveryQueue.get_nowait()
                
                timestamp = time.strftime("%H:%M:%S")
                if deliveryPacket.type == DeliveryPacketType.PACKET:
                    packet = deliveryPacket.data
                    display_msg = f"[{timestamp}] [Peer {packet.sender_id}] {packet.payload}"
                    self.add_to_history(display_msg)
                    received = True

                elif deliveryPacket.type == DeliveryPacketType.SYSTEM_MESSAGE:
                    self.add_system_message(deliveryPacket.data)

                else:
                    display_msg = f"[{timestamp}] {packet}"
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
        self.draw_input_area()

    def add_system_message(self, text):
        self.add_to_history(self.term.yellow(text))

    def read_line(self, prompt_text):
        buffer = []
        
        def draw_wizard_input():
            input_y = self.term.height - 1
            with self.term.location(0, input_y):
                print(self.term.clear_eol + prompt_text + "".join(buffer), end="", flush=True)
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
        try:
             self.add_system_message("--- SETUP WIZARD ---")
             
             # Peer ID
             ''' Unique Peer-ID per Peer over setup config'''
             if self.args.peerID:
                str_id = self.read_line(f"Current Peer ID is {self.args.peerID}. Enter new Peer ID (leave empty to keep current): ")
                if not str_id == "":
                    self.args.peerID = str_id
             else:
                 self.args.peerID = self.read_line(f"Enter Peer ID: ")
             
             # Port
             while True:
                 if self.args.port:
                     str_port = self.read_line(f"Current port is {self.args.port}. Enter new port (leave empty to keep current): ")
                     if str_port == "":
                         break
                 else:
                    str_port = self.read_line("Enter Port (int): ")
                 if str_port.isdigit():
                     self.args.port = int(str_port)
                     break
                 self.add_system_message("Invalid Port. Please enter a number.")
             
             # Peers File
             ''' List of Peer-IDs with Port and IP '''
             ''' Default group size of 5 peers '''
             while True:
                 if self.args.peers:
                     peers_file = self.read_line(f"Current peers file location is {self.args.port}. Enter new port (leave empty to keep current): ")
                     if peers_file == "":
                         break
                 else:
                    peers_file = self.read_line("Enter Peers File [peers.txt]: ")
                 if not peers_file.strip():
                     peers_file = "peers.txt"
                 try:
                     self.args.peers = utils.load_peer_config(peers_file)
                     break
                 except Exception as e:
                     self.add_system_message(f"Error loading file: {e}")
             
             # Initialize
             self.add_system_message("Initializing Middleware")

             self.args.log = f"peer{self.args.peerID}.log"

             # Actually init middleware
             self.mw = PeerMiddleware()
             
             # Init handler
             self.mw.start()

             self.configured = True
             self.prompt = f"(Peer {self.args.peerID}) >> "
             
             self.add_system_message("Setup Complete! System is now running.")
             self.add_system_message(f"Logging to {self.args.log}")
             
        except Exception as e:
            self.add_system_message(f"Setup Failed: {e}")
            import traceback
            traceback.print_exc()
