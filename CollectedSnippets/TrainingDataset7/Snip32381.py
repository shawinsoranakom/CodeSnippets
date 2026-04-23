def delete(self, name):
        name = self._path(name)
        try:
            os.remove(name)
        except FileNotFoundError:
            pass