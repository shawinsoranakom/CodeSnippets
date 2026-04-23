def serialize(self):
        """Full HTTP message, including headers, as a bytestring."""
        return self.serialize_headers() + b"\r\n\r\n" + self.content