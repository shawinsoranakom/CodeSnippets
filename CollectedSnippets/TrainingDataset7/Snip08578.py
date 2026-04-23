def seekable(self):
        if self.closed:
            return False
        if hasattr(self.file, "seekable"):
            return self.file.seekable()
        return True