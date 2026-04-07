def close(self):
            if not self.close_called:
                self.close_called = True
                try:
                    self.file.close()
                except OSError:
                    pass
                try:
                    self.unlink(self.name)
                except OSError:
                    pass