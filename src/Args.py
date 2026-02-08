from dataclasses import dataclass, field


@dataclass
class Args:
    _instance = None

    peerID: int = -1
    port: int = -1
    peers: dict = field(default_factory=dict)
    log: str = ""

    def __init__(self, peerID=None, port=None, peers=None, log=None):
        if getattr(self, '_initialized', False):
            return

        self._initialized = True

        self.peerID = peerID
        self.port = port
        self.peers = peers
        self.log = log

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance