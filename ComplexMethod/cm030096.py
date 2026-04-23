def exp(self, context=None):
        """Returns e ** self."""

        if context is None:
            context = getcontext()

        # exp(NaN) = NaN
        ans = self._check_nans(context=context)
        if ans:
            return ans

        # exp(-Infinity) = 0
        if self._isinfinity() == -1:
            return _Zero

        # exp(0) = 1
        if not self:
            return _One

        # exp(Infinity) = Infinity
        if self._isinfinity() == 1:
            return Decimal(self)

        # the result is now guaranteed to be inexact (the true
        # mathematical result is transcendental). There's no need to
        # raise Rounded and Inexact here---they'll always be raised as
        # a result of the call to _fix.
        p = context.prec
        adj = self.adjusted()

        # we only need to do any computation for quite a small range
        # of adjusted exponents---for example, -29 <= adj <= 10 for
        # the default context.  For smaller exponent the result is
        # indistinguishable from 1 at the given precision, while for
        # larger exponent the result either overflows or underflows.
        if self._sign == 0 and adj > len(str((context.Emax+1)*3)):
            # overflow
            ans = _dec_from_triple(0, '1', context.Emax+1)
        elif self._sign == 1 and adj > len(str((-context.Etiny()+1)*3)):
            # underflow to 0
            ans = _dec_from_triple(0, '1', context.Etiny()-1)
        elif self._sign == 0 and adj < -p:
            # p+1 digits; final round will raise correct flags
            ans = _dec_from_triple(0, '1' + '0'*(p-1) + '1', -p)
        elif self._sign == 1 and adj < -p-1:
            # p+1 digits; final round will raise correct flags
            ans = _dec_from_triple(0, '9'*(p+1), -p-1)
        # general case
        else:
            op = _WorkRep(self)
            c, e = op.int, op.exp
            if op.sign == 1:
                c = -c

            # compute correctly rounded result: increase precision by
            # 3 digits at a time until we get an unambiguously
            # roundable result
            extra = 3
            while True:
                coeff, exp = _dexp(c, e, p+extra)
                if coeff % (5*10**(len(str(coeff))-p-1)):
                    break
                extra += 3

            ans = _dec_from_triple(0, str(coeff), exp)

        # at this stage, ans should round correctly with *any*
        # rounding mode, not just with ROUND_HALF_EVEN
        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding

        return ans