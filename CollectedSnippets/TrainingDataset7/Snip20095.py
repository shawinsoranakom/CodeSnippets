def set_cookie(self, key, value, **kwargs):
        super().set_cookie(key, value, **kwargs)
        self._cookies_set.append(value)