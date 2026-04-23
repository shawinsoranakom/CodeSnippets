def max_mag(self, other, context=None):
        """Compares the values numerically with their sign ignored."""
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

        c = self.copy_abs()._cmp(other.copy_abs())
        if c == 0:
            c = self.compare_total(other)

        if c == -1:
            ans = other
        else:
            ans = self

        return ans._fix(context)