def __floordiv__(self, other, context=None):
        """self // other"""
        other = _convert_other(other)
        if other is NotImplemented:
            return other

        if context is None:
            context = getcontext()

        ans = self._check_nans(other, context)
        if ans:
            return ans

        if self._isinfinity():
            if other._isinfinity():
                return context._raise_error(InvalidOperation, 'INF // INF')
            else:
                return _SignedInfinity[self._sign ^ other._sign]

        if not other:
            if self:
                return context._raise_error(DivisionByZero, 'x // 0',
                                            self._sign ^ other._sign)
            else:
                return context._raise_error(DivisionUndefined, '0 // 0')

        return self._divide(other, context)[0]