def __call__(self, signal, sender, **kwargs):
        self.call_counter += 1
        self.call_args = kwargs