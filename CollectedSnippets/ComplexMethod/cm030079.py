def __truediv__(self, other, context=None):
        """Return self / other."""
        other = _convert_other(other)
        if other is NotImplemented:
            return NotImplemented

        if context is None:
            context = getcontext()

        sign = self._sign ^ other._sign

        if self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            if ans:
                return ans

            if self._isinfinity() and other._isinfinity():
                return context._raise_error(InvalidOperation, '(+-)INF/(+-)INF')

            if self._isinfinity():
                return _SignedInfinity[sign]

            if other._isinfinity():
                context._raise_error(Clamped, 'Division by infinity')
                return _dec_from_triple(sign, '0', context.Etiny())

        # Special cases for zeroes
        if not other:
            if not self:
                return context._raise_error(DivisionUndefined, '0 / 0')
            return context._raise_error(DivisionByZero, 'x / 0', sign)

        if not self:
            exp = self._exp - other._exp
            coeff = 0
        else:
            # OK, so neither = 0, INF or NaN
            shift = len(other._int) - len(self._int) + context.prec + 1
            exp = self._exp - other._exp - shift
            op1 = _WorkRep(self)
            op2 = _WorkRep(other)
            if shift >= 0:
                coeff, remainder = divmod(op1.int * 10**shift, op2.int)
            else:
                coeff, remainder = divmod(op1.int, op2.int * 10**-shift)
            if remainder:
                # result is not exact; adjust to ensure correct rounding
                if coeff % 5 == 0:
                    coeff += 1
            else:
                # result is exact; get as close to ideal exponent as possible
                ideal_exp = self._exp - other._exp
                while exp < ideal_exp and coeff % 10 == 0:
                    coeff //= 10
                    exp += 1

        ans = _dec_from_triple(sign, str(coeff), exp)
        return ans._fix(context)