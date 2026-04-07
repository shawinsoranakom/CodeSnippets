def __mul__(self, other):
        if isinstance(other, self.__class__):
            return Area(
                default_unit=AREA_PREFIX + self._default_unit,
                **{AREA_PREFIX + self.STANDARD_UNIT: (self.standard * other.standard)},
            )
        elif isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard * other)},
            )
        else:
            raise TypeError(
                "%(distance)s must be multiplied with number or %(distance)s"
                % {
                    "distance": pretty_name(self.__class__),
                }
            )