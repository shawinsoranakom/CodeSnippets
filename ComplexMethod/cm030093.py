def max(self, other, context=None):
        """Returns the larger value.

        Like max(self, other) except if one is not a number, returns
        NaN (and signals if one is sNaN).  Also rounds.
        """
        other = _convert_other(other, raiseit=True)

        if context is None:
            context = getcontext()

        if self._is_special or other._is_special:
            # If one operand is a quiet NaN and the other is number, then the
            # number is always returned
            sn = self._isnan()
            on = other._isnan()
            if sn or on:
                if on == 1 and sn == 0:
                    return self._fix(context)
                if sn == 1 and on == 0:
                    return other._fix(context)
                return self._check_nans(other, context)

        c = self._cmp(other)
        if c == 0:
            # If both operands are finite and equal in numerical value
            # then an ordering is applied:
            #
            # If the signs differ then max returns the operand with the
            # positive sign and min returns the operand with the negative sign
            #
            # If the signs are the same then the exponent is used to select
            # the result.  This is exactly the ordering used in compare_total.
            c = self.compare_total(other)

        if c == -1:
            ans = other
        else:
            ans = self

        return ans._fix(context)