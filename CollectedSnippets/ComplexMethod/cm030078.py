def __mul__(self, other, context=None):
        """Return self * other.

        (+-) INF * 0 (or its reverse) raise InvalidOperation.
        """
        other = _convert_other(other)
        if other is NotImplemented:
            return other

        if context is None:
            context = getcontext()

        resultsign = self._sign ^ other._sign

        if self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            if ans:
                return ans

            if self._isinfinity():
                if not other:
                    return context._raise_error(InvalidOperation, '(+-)INF * 0')
                return _SignedInfinity[resultsign]

            if other._isinfinity():
                if not self:
                    return context._raise_error(InvalidOperation, '0 * (+-)INF')
                return _SignedInfinity[resultsign]

        resultexp = self._exp + other._exp

        # Special case for multiplying by zero
        if not self or not other:
            ans = _dec_from_triple(resultsign, '0', resultexp)
            # Fixing in case the exponent is out of bounds
            ans = ans._fix(context)
            return ans

        # Special case for multiplying by power of 10
        if self._int == '1':
            ans = _dec_from_triple(resultsign, other._int, resultexp)
            ans = ans._fix(context)
            return ans
        if other._int == '1':
            ans = _dec_from_triple(resultsign, self._int, resultexp)
            ans = ans._fix(context)
            return ans

        op1 = _WorkRep(self)
        op2 = _WorkRep(other)

        ans = _dec_from_triple(resultsign, str(op1.int * op2.int), resultexp)
        ans = ans._fix(context)

        return ans