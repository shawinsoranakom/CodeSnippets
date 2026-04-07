def _relative_path(self, name):
        full_path = self.path(name)
        return os.path.relpath(full_path, self.location)