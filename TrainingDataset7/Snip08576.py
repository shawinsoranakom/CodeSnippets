def readable(self):
        if self.closed:
            return False
        if hasattr(self.file, "readable"):
            return self.file.readable()
        return True