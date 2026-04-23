def chunks(self, chunk_size=None):
        self.file.seek(0)
        yield self.read()