def writable(self):
        if self.closed:
            return False
        if hasattr(self.file, "writable"):
            return self.file.writable()
        return "w" in getattr(self.file, "mode", "")