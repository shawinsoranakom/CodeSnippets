def __init__(self, signal):
        self.call_counter = 0
        self.call_args = None
        signal.connect(self, sender=APP_CONFIG)