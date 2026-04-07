def receive_data_chunk(self, raw_data, start):
        """Add the data to the BytesIO file."""
        if self.activated:
            self.file.write(raw_data)
        else:
            return raw_data