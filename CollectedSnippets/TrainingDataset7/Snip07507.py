def __isub__(self, other):
        if isinstance(other, self.__class__):
            self.standard -= other.standard
            return self
        else:
            raise TypeError(
                "%(class)s must be subtracted from %(class)s"
                % {"class": pretty_name(self)}
            )