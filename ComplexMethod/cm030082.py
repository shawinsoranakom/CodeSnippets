def remainder_near(self, other, context=None):
        """
        Remainder nearest to 0-  abs(remainder-near) <= other/2
        """
        if context is None:
            context = getcontext()

        other = _convert_other(other, raiseit=True)

        ans = self._check_nans(other, context)
        if ans:
            return ans

        # self == +/-infinity -> InvalidOperation
        if self._isinfinity():
            return context._raise_error(InvalidOperation,
                                        'remainder_near(infinity, x)')

        # other == 0 -> either InvalidOperation or DivisionUndefined
        if not other:
            if self:
                return context._raise_error(InvalidOperation,
                                            'remainder_near(x, 0)')
            else:
                return context._raise_error(DivisionUndefined,
                                            'remainder_near(0, 0)')

        # other = +/-infinity -> remainder = self
        if other._isinfinity():
            ans = Decimal(self)
            return ans._fix(context)

        # self = 0 -> remainder = self, with ideal exponent
        ideal_exponent = min(self._exp, other._exp)
        if not self:
            ans = _dec_from_triple(self._sign, '0', ideal_exponent)
            return ans._fix(context)

        # catch most cases of large or small quotient
        expdiff = self.adjusted() - other.adjusted()
        if expdiff >= context.prec + 1:
            # expdiff >= prec+1 => abs(self/other) > 10**prec
            return context._raise_error(DivisionImpossible)
        if expdiff <= -2:
            # expdiff <= -2 => abs(self/other) < 0.1
            ans = self._rescale(ideal_exponent, context.rounding)
            return ans._fix(context)

        # adjust both arguments to have the same exponent, then divide
        op1 = _WorkRep(self)
        op2 = _WorkRep(other)
        if op1.exp >= op2.exp:
            op1.int *= 10**(op1.exp - op2.exp)
        else:
            op2.int *= 10**(op2.exp - op1.exp)
        q, r = divmod(op1.int, op2.int)
        # remainder is r*10**ideal_exponent; other is +/-op2.int *
        # 10**ideal_exponent.   Apply correction to ensure that
        # abs(remainder) <= abs(other)/2
        if 2*r + (q&1) > op2.int:
            r -= op2.int
            q += 1

        if q >= 10**context.prec:
            return context._raise_error(DivisionImpossible)

        # result has same sign as self unless r is negative
        sign = self._sign
        if r < 0:
            sign = 1-sign
            r = -r

        ans = _dec_from_triple(sign, str(r), ideal_exponent)
        return ans._fix(context)