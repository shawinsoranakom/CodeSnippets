def exists(self, name):
        return os.path.lexists(self.path(name))