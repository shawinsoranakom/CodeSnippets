def next_toward(self, other, context=None):
        """Returns the number closest to self, in the direction towards other.

        The result is the closest representable number to self
        (excluding self) that is in the direction towards other,
        unless both have the same value.  If the two operands are
        numerically equal, then the result is a copy of self with the
        sign set to be the same as the sign of other.
        """
        other = _convert_other(other, raiseit=True)

        if context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        if ans:
            return ans

        comparison = self._cmp(other)
        if comparison == 0:
            return self.copy_sign(other)

        if comparison == -1:
            ans = self.next_plus(context)
        else: # comparison == 1
            ans = self.next_minus(context)

        # decide which flags to raise using value of ans
        if ans._isinfinity():
            context._raise_error(Overflow,
                                 'Infinite result from next_toward',
                                 ans._sign)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
        elif ans.adjusted() < context.Emin:
            context._raise_error(Underflow)
            context._raise_error(Subnormal)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
            # if precision == 1 then we don't raise Clamped for a
            # result 0E-Etiny.
            if not ans:
                context._raise_error(Clamped)

        return ans