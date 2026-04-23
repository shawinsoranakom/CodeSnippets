def url(self):
        self._require_file()
        return self.storage.url(self.name)