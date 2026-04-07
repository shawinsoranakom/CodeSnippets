def path(self):
        self._require_file()
        return self.storage.path(self.name)