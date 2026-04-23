def shift(self, other, context=None):
        """Returns a shifted copy of self, value-of-other times."""
        if context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        if ans:
            return ans

        if other._exp != 0:
            return context._raise_error(InvalidOperation)
        if not (-context.prec <= int(other) <= context.prec):
            return context._raise_error(InvalidOperation)

        if self._isinfinity():
            return Decimal(self)

        # get values, pad if necessary
        torot = int(other)
        rotdig = self._int
        topad = context.prec - len(rotdig)
        if topad > 0:
            rotdig = '0'*topad + rotdig
        elif topad < 0:
            rotdig = rotdig[-topad:]

        # let's shift!
        if torot < 0:
            shifted = rotdig[:torot]
        else:
            shifted = rotdig + '0'*torot
            shifted = shifted[-context.prec:]

        return _dec_from_triple(self._sign,
                                    shifted.lstrip('0') or '0', self._exp)