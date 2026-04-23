def _divide(self, other, context):
        """Return (self // other, self % other), to context.prec precision.

        Assumes that neither self nor other is a NaN, that self is not
        infinite and that other is nonzero.
        """
        sign = self._sign ^ other._sign
        if other._isinfinity():
            ideal_exp = self._exp
        else:
            ideal_exp = min(self._exp, other._exp)

        expdiff = self.adjusted() - other.adjusted()
        if not self or other._isinfinity() or expdiff <= -2:
            return (_dec_from_triple(sign, '0', 0),
                    self._rescale(ideal_exp, context.rounding))
        if expdiff <= context.prec:
            op1 = _WorkRep(self)
            op2 = _WorkRep(other)
            if op1.exp >= op2.exp:
                op1.int *= 10**(op1.exp - op2.exp)
            else:
                op2.int *= 10**(op2.exp - op1.exp)
            q, r = divmod(op1.int, op2.int)
            if q < 10**context.prec:
                return (_dec_from_triple(sign, str(q), 0),
                        _dec_from_triple(self._sign, str(r), ideal_exp))

        # Here the quotient is too large to be representable
        ans = context._raise_error(DivisionImpossible,
                                   'quotient too large in //, % or divmod')
        return ans, ans