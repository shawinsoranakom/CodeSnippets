def open(self, mode="rb"):
        self._require_file()
        if getattr(self, "_file", None) is None:
            self.file = self.storage.open(self.name, mode)
        else:
            self.file.open(mode)
        return self