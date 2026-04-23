def __init__(self, dim=2, trim=False, precision=None):
        super().__init__()
        self._trim = DEFAULT_TRIM_VALUE
        self.trim = trim
        if precision is not None:
            self.precision = precision
        self.outdim = dim