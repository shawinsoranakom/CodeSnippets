def pop(self, key, *args):
        self._assert_mutable()
        return super().pop(key, *args)