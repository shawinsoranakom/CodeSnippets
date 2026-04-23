def exists(self, name):
        return self._resolve(name, check_exists=False) is not None