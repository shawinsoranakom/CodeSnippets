def __init__(self, *, assume_scheme=None, **kwargs):
        self.assume_scheme = assume_scheme or "https"
        super().__init__(strip=True, **kwargs)