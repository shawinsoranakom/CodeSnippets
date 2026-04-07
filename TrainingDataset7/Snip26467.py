def __getattribute__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            return getattr(self._request, attr)