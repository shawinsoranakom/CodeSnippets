def size(self, name):
        return len(self._open(name, "rb").file.getvalue())