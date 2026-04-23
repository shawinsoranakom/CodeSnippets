def __getitem__(self, index):
        "Get the item(s) at the specified index/slice."
        if isinstance(index, slice):
            return [
                self._get_single_external(i) for i in range(*index.indices(len(self)))
            ]
        else:
            index = self._checkindex(index)
            return self._get_single_external(index)