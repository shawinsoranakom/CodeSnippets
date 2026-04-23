def __eq__(self, other):
        if not isinstance(other, HashKey):
            return NotImplemented

        if self._crasher is not None and self._crasher.error_on_eq:
            raise EqError

        if self.error_on_eq_to is not None and self.error_on_eq_to is other:
            raise ValueError(f'cannot compare {self!r} to {other!r}')
        if other.error_on_eq_to is not None and other.error_on_eq_to is self:
            raise ValueError(f'cannot compare {other!r} to {self!r}')

        return (self.name, self.hash) == (other.name, other.hash)