def size(self):
        if hasattr(self.file, "size"):
            return self.file.size
        if hasattr(self.file, "name"):
            try:
                return os.path.getsize(self.file.name)
            except (OSError, TypeError):
                pass
        if hasattr(self.file, "tell") and hasattr(self.file, "seek"):
            pos = self.file.tell()
            self.file.seek(0, os.SEEK_END)
            size = self.file.tell()
            self.file.seek(pos)
            return size
        raise AttributeError("Unable to determine the file's size.")