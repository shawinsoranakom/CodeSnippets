def close(self):
                self._closed.append(True)
                self.f.close()