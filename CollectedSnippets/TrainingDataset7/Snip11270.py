def size(self):
        self._require_file()
        if not self._committed:
            return self.file.size
        return self.storage.size(self.name)