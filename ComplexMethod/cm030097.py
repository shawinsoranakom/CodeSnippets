def ln(self, context=None):
        """Returns the natural (base e) logarithm of self."""

        if context is None:
            context = getcontext()

        # ln(NaN) = NaN
        ans = self._check_nans(context=context)
        if ans:
            return ans

        # ln(0.0) == -Infinity
        if not self:
            return _NegativeInfinity

        # ln(Infinity) = Infinity
        if self._isinfinity() == 1:
            return _Infinity

        # ln(1.0) == 0.0
        if self == _One:
            return _Zero

        # ln(negative) raises InvalidOperation
        if self._sign == 1:
            return context._raise_error(InvalidOperation,
                                        'ln of a negative value')

        # result is irrational, so necessarily inexact
        op = _WorkRep(self)
        c, e = op.int, op.exp
        p = context.prec

        # correctly rounded result: repeatedly increase precision by 3
        # until we get an unambiguously roundable result
        places = p - self._ln_exp_bound() + 2 # at least p+3 places
        while True:
            coeff = _dlog(c, e, places)
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