def __imul__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.standard *= float(other)
            return self
        else:
            raise TypeError(
                "%(class)s must be multiplied with number"
                % {"class": pretty_name(self)}
            )