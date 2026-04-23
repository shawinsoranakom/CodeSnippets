def __mul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard * other)},
            )
        else:
            raise TypeError(
                "%(class)s must be multiplied with number"
                % {"class": pretty_name(self)}
            )