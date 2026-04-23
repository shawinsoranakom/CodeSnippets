def as_integer_ratio(self):
        """Express a finite Decimal instance in the form n / d.

        Returns a pair (n, d) of integers.  When called on an infinity
        or NaN, raises OverflowError or ValueError respectively.

        >>> Decimal('3.14').as_integer_ratio()
        (157, 50)
        >>> Decimal('-123e5').as_integer_ratio()
        (-12300000, 1)
        >>> Decimal('0.00').as_integer_ratio()
        (0, 1)

        """
        if self._is_special:
            if self.is_nan():
                raise ValueError("cannot convert NaN to integer ratio")
            else:
                raise OverflowError("cannot convert Infinity to integer ratio")

        if not self:
            return 0, 1

        # Find n, d in lowest terms such that abs(self) == n / d;
        # we'll deal with the sign later.
        n = int(self._int)
        if self._exp >= 0:
            # self is an integer.
            n, d = n * 10**self._exp, 1
        else:
            # Find d2, d5 such that abs(self) = n / (2**d2 * 5**d5).
            d5 = -self._exp
            while d5 > 0 and n % 5 == 0:
                n //= 5
                d5 -= 1

            # (n & -n).bit_length() - 1 counts trailing zeros in binary
            # representation of n (provided n is nonzero).
            d2 = -self._exp
            shift2 = min((n & -n).bit_length() - 1, d2)
            if shift2:
                n >>= shift2
                d2 -= shift2

            d = 5**d5 << d2

        if self._sign:
            n = -n
        return n, d