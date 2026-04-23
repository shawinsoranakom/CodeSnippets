def compare_total(self, other, context=None):
        """Compares self to other using the abstract representations.

        This is not like the standard compare, which use their numerical
        value. Note that a total ordering is defined for all possible abstract
        representations.
        """
        other = _convert_other(other, raiseit=True)

        # if one is negative and the other is positive, it's easy
        if self._sign and not other._sign:
            return _NegativeOne
        if not self._sign and other._sign:
            return _One
        sign = self._sign

        # let's handle both NaN types
        self_nan = self._isnan()
        other_nan = other._isnan()
        if self_nan or other_nan:
            if self_nan == other_nan:
                # compare payloads as though they're integers
                self_key = len(self._int), self._int
                other_key = len(other._int), other._int
                if self_key < other_key:
                    if sign:
                        return _One
                    else:
                        return _NegativeOne
                if self_key > other_key:
                    if sign:
                        return _NegativeOne
                    else:
                        return _One
                return _Zero

            if sign:
                if self_nan == 1:
                    return _NegativeOne
                if other_nan == 1:
                    return _One
                if self_nan == 2:
                    return _NegativeOne
                if other_nan == 2:
                    return _One
            else:
                if self_nan == 1:
                    return _One
                if other_nan == 1:
                    return _NegativeOne
                if self_nan == 2:
                    return _One
                if other_nan == 2:
                    return _NegativeOne

        if self < other:
            return _NegativeOne
        if self > other:
            return _One

        if self._exp < other._exp:
            if sign:
                return _One
            else:
                return _NegativeOne
        if self._exp > other._exp:
            if sign:
                return _NegativeOne
            else:
                return _One
        return _Zero