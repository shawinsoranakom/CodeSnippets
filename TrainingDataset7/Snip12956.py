def serialize_headers(self):
        """HTTP headers as a bytestring."""
        return b"\r\n".join(
            [
                key.encode("ascii") + b": " + value.encode("latin-1")
                for key, value in self.headers.items()
            ]
        )