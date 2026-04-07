def clear(self):
        """
        Remove all the cache files.
        """
        for fname in self._list_cache_files():
            self._delete(fname)