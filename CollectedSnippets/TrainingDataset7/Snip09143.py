def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.max_digits == other.max_digits
            and self.decimal_places == other.decimal_places
        )