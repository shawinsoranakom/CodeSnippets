def close(self):
                if self._file:
                    self._file.close()
                    self._file = None