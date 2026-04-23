def __setitem__(self, index, val):
        "Set the item(s) at the specified index/slice."
        if isinstance(index, slice):
            self._set_slice(index, val)
        else:
            index = self._checkindex(index)
            self._check_allowed((val,))
            self._set_single(index, val)