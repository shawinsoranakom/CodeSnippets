def __add__(self, other, context=None):
        """Returns self + other.

        -INF + INF (or the reverse) cause InvalidOperation errors.
        """
        other = _convert_other(other)
        if other is NotImplemented:
            return other

        if context is None:
            context = getcontext()

        if self._is_special or other._is_special:
            ans = self._check_nans(other, context)
            if ans:
                return ans

            if self._isinfinity():
                # If both INF, same sign => same as both, opposite => error.
                if self._sign != other._sign and other._isinfinity():
                    return context._raise_error(InvalidOperation, '-INF + INF')
                return Decimal(self)
            if other._isinfinity():
                return Decimal(other)  # Can't both be infinity here

        exp = min(self._exp, other._exp)
        negativezero = 0
        if context.rounding == ROUND_FLOOR and self._sign != other._sign:
            # If the answer is 0, the sign should be negative, in this case.
            negativezero = 1

        if not self and not other:
            sign = min(self._sign, other._sign)
            if negativezero:
                sign = 1
            ans = _dec_from_triple(sign, '0', exp)
            ans = ans._fix(context)
            return ans
        if not self:
            exp = max(exp, other._exp - context.prec-1)
            ans = other._rescale(exp, context.rounding)
            ans = ans._fix(context)
            return ans
        if not other:
            exp = max(exp, self._exp - context.prec-1)
            ans = self._rescale(exp, context.rounding)
            ans = ans._fix(context)
            return ans

        op1 = _WorkRep(self)
        op2 = _WorkRep(other)
        op1, op2 = _normalize(op1, op2, context.prec)

        result = _WorkRep()
        if op1.sign != op2.sign:
            # Equal and opposite
            if op1.int == op2.int:
                ans = _dec_from_triple(negativezero, '0', exp)
                ans = ans._fix(context)
                return ans
            if op1.int < op2.int:
                op1, op2 = op2, op1
                # OK, now abs(op1) > abs(op2)
            if op1.sign == 1:
                result.sign = 1
                op1.sign, op2.sign = op2.sign, op1.sign
            else:
                result.sign = 0
                # So we know the sign, and op1 > 0.
        elif op1.sign == 1:
            result.sign = 1
            op1.sign, op2.sign = (0, 0)
        else:
            result.sign = 0
        # Now, op1 > abs(op2) > 0

        if op2.sign == 0:
            result.int = op1.int + op2.int
        else:
            result.int = op1.int - op2.int

        result.exp = op1.exp
        ans = Decimal(result)
        ans = ans._fix(context)
        return ans