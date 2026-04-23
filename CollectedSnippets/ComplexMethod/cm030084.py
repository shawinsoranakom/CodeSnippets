def _fix(self, context):
        """Round if it is necessary to keep self within prec precision.

        Rounds and fixes the exponent.  Does not raise on a sNaN.

        Arguments:
        self - Decimal instance
        context - context used.
        """

        if self._is_special:
            if self._isnan():
                # decapitate payload if necessary
                return self._fix_nan(context)
            else:
                # self is +/-Infinity; return unaltered
                return Decimal(self)

        # if self is zero then exponent should be between Etiny and
        # Emax if clamp==0, and between Etiny and Etop if clamp==1.
        Etiny = context.Etiny()
        Etop = context.Etop()
        if not self:
            exp_max = [context.Emax, Etop][context.clamp]
            new_exp = min(max(self._exp, Etiny), exp_max)
            if new_exp != self._exp:
                context._raise_error(Clamped)
                return _dec_from_triple(self._sign, '0', new_exp)
            else:
                return Decimal(self)

        # exp_min is the smallest allowable exponent of the result,
        # equal to max(self.adjusted()-context.prec+1, Etiny)
        exp_min = len(self._int) + self._exp - context.prec
        if exp_min > Etop:
            # overflow: exp_min > Etop iff self.adjusted() > Emax
            ans = context._raise_error(Overflow, 'above Emax', self._sign)
            context._raise_error(Inexact)
            context._raise_error(Rounded)
            return ans

        self_is_subnormal = exp_min < Etiny
        if self_is_subnormal:
            exp_min = Etiny

        # round if self has too many digits
        if self._exp < exp_min:
            digits = len(self._int) + self._exp - exp_min
            if digits < 0:
                self = _dec_from_triple(self._sign, '1', exp_min-1)
                digits = 0
            rounding_method = self._pick_rounding_function[context.rounding]
            changed = rounding_method(self, digits)
            coeff = self._int[:digits] or '0'
            if changed > 0:
                coeff = str(int(coeff)+1)
                if len(coeff) > context.prec:
                    coeff = coeff[:-1]
                    exp_min += 1

            # check whether the rounding pushed the exponent out of range
            if exp_min > Etop:
                ans = context._raise_error(Overflow, 'above Emax', self._sign)
            else:
                ans = _dec_from_triple(self._sign, coeff, exp_min)

            # raise the appropriate signals, taking care to respect
            # the precedence described in the specification
            if changed and self_is_subnormal:
                context._raise_error(Underflow)
            if self_is_subnormal:
                context._raise_error(Subnormal)
            if changed:
                context._raise_error(Inexact)
            context._raise_error(Rounded)
            if not ans:
                # raise Clamped on underflow to 0
                context._raise_error(Clamped)
            return ans

        if self_is_subnormal:
            context._raise_error(Subnormal)

        # fold down if clamp == 1 and self has too few digits
        if context.clamp == 1 and self._exp > Etop:
            context._raise_error(Clamped)
            self_padded = self._int + '0'*(self._exp - Etop)
            return _dec_from_triple(self._sign, self_padded, Etop)

        # here self was representable to begin with; return unchanged
        return Decimal(self)