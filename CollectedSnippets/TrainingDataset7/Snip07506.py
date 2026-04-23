def __sub__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(
                default_unit=self._default_unit,
                **{self.STANDARD_UNIT: (self.standard - other.standard)},
            )
        else:
            raise TypeError(
                "%(class)s must be subtracted from %(class)s"
                % {"class": pretty_name(self)}
            )