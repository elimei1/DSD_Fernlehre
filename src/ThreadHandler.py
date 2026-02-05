import threading


class ThreadHandler:

    def __init__(self, middleware):
        self.sender_threads = []
        self.receiver_threads = []
        self.reaper_threads = []
        self.preProcessingThreads = []
        self.middleware = middleware

    def startSenderThread(self):
        thread = threading.Thread(target=self.middleware.sender_thread)
        self.sender_threads.append(thread)
        thread.start()


    def startReceiverThread(self):
        thread = threading.Thread(target=self.middleware.receiver_thread)
        self.sender_threads.append(thread)
        thread.start()

    def startReaperThread(self):
        thread = threading.Thread(target=self.middleware.reaper_thread)
        self.sender_threads.append(thread)
        thread.start()

    def startPreProcessingThread(self):
        thread = threading.Thread(target=self.middleware.preProcessing_thread)
        self.sender_threads.append(thread)
        thread.start()

    def shutdown(self):
        self.middleware.running = False
        for t in self.sender_threads + self.receiver_threads + self.reaper_threads + self.preProcessingThreads:
            if t.is_alive():
                t.join(timeout=5.0)