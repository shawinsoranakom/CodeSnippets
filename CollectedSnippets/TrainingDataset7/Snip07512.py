def __itruediv__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            self.standard /= float(other)
            return self
        else:
            raise TypeError(
                "%(class)s must be divided with number" % {"class": pretty_name(self)}
            )