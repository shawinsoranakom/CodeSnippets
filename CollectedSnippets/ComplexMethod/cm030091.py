def to_integral_exact(self, rounding=None, context=None):
        """Rounds to a nearby integer.

        If no rounding mode is specified, take the rounding mode from
        the context.  This method raises the Rounded and Inexact flags
        when appropriate.

        See also: to_integral_value, which does exactly the same as
        this method except that it doesn't raise Inexact or Rounded.
        """
        if self._is_special:
            ans = self._check_nans(context=context)
            if ans:
                return ans
            return Decimal(self)
        if self._exp >= 0:
            return Decimal(self)
        if not self:
            return _dec_from_triple(self._sign, '0', 0)
        if context is None:
            context = getcontext()
        if rounding is None:
            rounding = context.rounding
        ans = self._rescale(0, rounding)
        if ans != self:
            context._raise_error(Inexact)
        context._raise_error(Rounded)
        return ans