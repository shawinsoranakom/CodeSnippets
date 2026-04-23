def __delitem__(self, key):
        self._assert_mutable()
        super().__delitem__(key)