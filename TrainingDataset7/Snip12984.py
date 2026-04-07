def write(self, content):
        self._container.append(self.make_bytes(content))