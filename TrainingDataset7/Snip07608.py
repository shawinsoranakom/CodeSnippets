def decode(self, s, **kwargs):
        decoded = super().decode(s, **kwargs)
        return self.process_messages(decoded)