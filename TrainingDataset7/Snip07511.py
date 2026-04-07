def __truediv__(self, other):
        if isinstance(other, self.__class__):
            return self.standard / other.standard
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard / other)},
            )
        else:
            raise TypeError(
                "%(class)s must be divided with number or %(class)s"
                % {"class": pretty_name(self)}
            )