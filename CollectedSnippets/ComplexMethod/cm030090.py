def quantize(self, exp, rounding=None, context=None):
        """Quantize self so its exponent is the same as that of exp.

        Similar to self._rescale(exp._exp) but with error checking.
        """
        exp = _convert_other(exp, raiseit=True)

        if context is None:
            context = getcontext()
        if rounding is None:
            rounding = context.rounding

        if self._is_special or exp._is_special:
            ans = self._check_nans(exp, context)
            if ans:
                return ans

            if exp._isinfinity() or self._isinfinity():
                if exp._isinfinity() and self._isinfinity():
                    return Decimal(self)  # if both are inf, it is OK
                return context._raise_error(InvalidOperation,
                                        'quantize with one INF')

        # exp._exp should be between Etiny and Emax
        if not (context.Etiny() <= exp._exp <= context.Emax):
            return context._raise_error(InvalidOperation,
                   'target exponent out of bounds in quantize')

        if not self:
            ans = _dec_from_triple(self._sign, '0', exp._exp)
            return ans._fix(context)

        self_adjusted = self.adjusted()
        if self_adjusted > context.Emax:
            return context._raise_error(InvalidOperation,
                                        'exponent of quantize result too large for current context')
        if self_adjusted - exp._exp + 1 > context.prec:
            return context._raise_error(InvalidOperation,
                                        'quantize result has too many digits for current context')

        ans = self._rescale(exp._exp, rounding)
        if ans.adjusted() > context.Emax:
            return context._raise_error(InvalidOperation,
                                        'exponent of quantize result too large for current context')
        if len(ans._int) > context.prec:
            return context._raise_error(InvalidOperation,
                                        'quantize result has too many digits for current context')

        # raise appropriate flags
        if ans and ans.adjusted() < context.Emin:
            context._raise_error(Subnormal)
        if ans._exp > self._exp:
            if ans != self:
                context._raise_error(Inexact)
            context._raise_error(Rounded)

        # call to fix takes care of any necessary folddown, and
        # signals Clamped if necessary
        ans = ans._fix(context)
        return ans