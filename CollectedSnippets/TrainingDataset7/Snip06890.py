def __eq__(self, other):
        """
        Return True if the envelopes are equivalent; can compare against
        other Envelopes and 4-tuples.
        """
        if isinstance(other, Envelope):
            return (
                (self.min_x == other.min_x)
                and (self.min_y == other.min_y)
                and (self.max_x == other.max_x)
                and (self.max_y == other.max_y)
            )
        elif isinstance(other, tuple) and len(other) == 4:
            return (
                (self.min_x == other[0])
                and (self.min_y == other[1])
                and (self.max_x == other[2])
                and (self.max_y == other[3])
            )
        else:
            raise GDALException("Equivalence testing only works with other Envelopes.")