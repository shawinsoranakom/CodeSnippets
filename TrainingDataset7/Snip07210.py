def __getitem__(self, index):
        "Return the coordinate sequence value at the given index."
        self._checkindex(index)
        return self._point_getter(index)