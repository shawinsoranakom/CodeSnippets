def _open(self, name, mode="rb"):
        return File(open(self.path(name), mode))