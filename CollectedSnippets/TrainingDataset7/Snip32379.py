def exists(self, name):
        return os.path.exists(self._path(name))