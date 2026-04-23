def __divmod__(self, other, context=None):
        """
        Return (self // other, self % other)
        """
        other = _convert_other(other)
        if other is NotImplemented:
            return other

        if context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        if ans:
            return (ans, ans)

        sign = self._sign ^ other._sign
        if self._isinfinity():
            if other._isinfinity():
                ans = context._raise_error(InvalidOperation, 'divmod(INF, INF)')
                return ans, ans
            else:
                return (_SignedInfinity[sign],
                        context._raise_error(InvalidOperation, 'INF % x'))

        if not other:
            if not self:
                ans = context._raise_error(DivisionUndefined, 'divmod(0, 0)')
                return ans, ans
            else:
                return (context._raise_error(DivisionByZero, 'x // 0', sign),
                        context._raise_error(InvalidOperation, 'x % 0'))

        quotient, remainder = self._divide(other, context)
        remainder = remainder._fix(context)
        return quotient, remainder