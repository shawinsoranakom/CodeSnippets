def __setitem__(self, key, val):
        if self._readonly:
            raise error('The database is opened for reading only')
        if isinstance(key, str):
            key = key.encode('utf-8')
        elif not isinstance(key, (bytes, bytearray)):
            raise TypeError("keys must be bytes or strings")
        if isinstance(val, str):
            val = val.encode('utf-8')
        elif not isinstance(val, (bytes, bytearray)):
            raise TypeError("values must be bytes or strings")
        self._verify_open()
        self._modified = True
        if key not in self._index:
            self._addkey(key, self._addval(val))
        else:
            # See whether the new value is small enough to fit in the
            # (padded) space currently occupied by the old value.
            pos, siz = self._index[key]
            oldblocks = (siz + _BLOCKSIZE - 1) // _BLOCKSIZE
            newblocks = (len(val) + _BLOCKSIZE - 1) // _BLOCKSIZE
            if newblocks <= oldblocks:
                self._index[key] = self._setval(pos, val)
            else:
                # The new value doesn't fit in the (padded) space used
                # by the old value.  The blocks used by the old value are
                # forever lost.
                self._index[key] = self._addval(val)