def __init__(self, signal):
        self.signal = signal
        self.call_counter = 0
        self.call_args = None
        self.signal.connect(self, sender=APP_CONFIG)