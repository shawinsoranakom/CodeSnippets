def __hash__(self):
        # Hash the path only, to ensure performant comparison in Media.merge.
        return hash(self._path)