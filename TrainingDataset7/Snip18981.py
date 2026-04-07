def _write(self, data):
        if self.headers_written:
            self.write_chunk_counter += 1
        self.stdout.write(data)