def get_protocol(self, protocol=None):
        # Determine protocol
        return self.protocol or protocol or "https"