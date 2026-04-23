def _cmp(self, other):
        """Compare the two non-NaN decimal instances self and other.

        Returns -1 if self < other, 0 if self == other and 1
        if self > other.  This routine is for internal use only."""

        if self._is_special or other._is_special:
            self_inf = self._isinfinity()
            other_inf = other._isinfinity()
            if self_inf == other_inf:
                return 0
            elif self_inf < other_inf:
                return -1
            else:
                return 1

        # check for zeros;  Decimal('0') == Decimal('-0')
        if not self:
            if not other:
                return 0
            else:
                return -((-1)**other._sign)
        if not other:
            return (-1)**self._sign

        # If different signs, neg one is less
        if other._sign < self._sign:
            return -1
        if self._sign < other._sign:
            return 1

        self_adjusted = self.adjusted()
        other_adjusted = other.adjusted()
        if self_adjusted == other_adjusted:
            self_padded = self._int + '0'*(self._exp - other._exp)
            other_padded = other._int + '0'*(other._exp - self._exp)
            if self_padded == other_padded:
                return 0
            elif self_padded < other_padded:
                return -(-1)**self._sign
            else:
                return (-1)**self._sign
        elif self_adjusted > other_adjusted:
            return (-1)**self._sign
        else: # self_adjusted < other_adjusted
            return -((-1)**self._sign)