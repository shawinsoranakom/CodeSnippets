def setlistdefault(self, key, default_list=None):
        self._assert_mutable()
        return super().setlistdefault(key, default_list)