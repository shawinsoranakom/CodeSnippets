def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._cookies_set.append(value)