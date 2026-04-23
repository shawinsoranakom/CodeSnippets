def open(self):
        if self.stream is None:
            self.stream = open(self._get_filename(), "ab")
            return True
        return False