def seek(self, offset, whence=io.SEEK_SET):
                return self._file.seek(offset, whence)