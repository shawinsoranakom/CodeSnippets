def log10(self, context=None):
        """Returns the base 10 logarithm of self."""

        if context is None:
            context = getcontext()

        # log10(NaN) = NaN
        ans = self._check_nans(context=context)
        if ans:
            return ans

        # log10(0.0) == -Infinity
        if not self:
            return _NegativeInfinity

        # log10(Infinity) = Infinity
        if self._isinfinity() == 1:
            return _Infinity

        # log10(negative or -Infinity) raises InvalidOperation
        if self._sign == 1:
            return context._raise_error(InvalidOperation,
                                        'log10 of a negative value')

        # log10(10**n) = n
        if self._int[0] == '1' and self._int[1:] == '0'*(len(self._int) - 1):
            # answer may need rounding
            ans = Decimal(self._exp + len(self._int) - 1)
        else:
            # result is irrational, so necessarily inexact
            op = _WorkRep(self)
            c, e = op.int, op.exp
            p = context.prec

            # correctly rounded result: repeatedly increase precision
            # until result is unambiguously roundable
            places = p-self._log10_exp_bound()+2
            while True:
                coeff = _dlog10(c, e, places)
                # assert len(str(abs(coeff)))-p >= 1
                if coeff % (5*10**(len(str(abs(coeff)))-p-1)):
                    break
                places += 3
            ans = _dec_from_triple(int(coeff<0), str(abs(coeff)), -places)

        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding
        return ans