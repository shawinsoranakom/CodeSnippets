def __eq__(self, other):
        # Compare the path only, to ensure performant comparison in
        # Media.merge.
        return (self.__class__ is other.__class__ and self.path == other.path) or (
            isinstance(other, str) and self._path == other
        )