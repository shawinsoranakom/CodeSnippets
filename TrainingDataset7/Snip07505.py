def __iadd__(self, other):
        if isinstance(other, self.__class__):
            self.standard += other.standard
            return self
        else:
            raise TypeError(
                "%(class)s must be added with %(class)s" % {"class": pretty_name(self)}
            )