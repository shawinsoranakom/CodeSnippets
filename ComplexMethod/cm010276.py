def __call__(self, min=None, max=None) -> "_DimHint":
        if not self._factory:
            raise TypeError(f"'{type(self)}' object is not callable")
        if min is not None and min < 0:
            raise AssertionError(f"min must be non-negative, got {min}")
        if max is not None and max < 0:
            raise AssertionError(f"max must be non-negative, got {max}")
        if min is not None and max is not None and min > max:
            raise AssertionError(f"min must be <= max, got min={min}, max={max}")
        return _DimHint(self.type, min=min, max=max, _factory=False)