def __init__(self, default_unit=None, **kwargs):
        value, self._default_unit = self.default_units(kwargs)
        setattr(self, self.STANDARD_UNIT, value)
        if default_unit and isinstance(default_unit, str):
            self._default_unit = default_unit