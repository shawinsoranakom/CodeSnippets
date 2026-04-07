def close(self):
        try:
            if self.stream is not None:
                self.stream.close()
        finally:
            self.stream = None