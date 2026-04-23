def __pow__(self, other, modulo=None, context=None):
        """Return self ** other [ % modulo].

        With two arguments, compute self**other.

        With three arguments, compute (self**other) % modulo.  For the
        three argument form, the following restrictions on the
        arguments hold:

         - all three arguments must be integral
         - other must be nonnegative
         - either self or other (or both) must be nonzero
         - modulo must be nonzero and must have at most p digits,
           where p is the context precision.

        If any of these restrictions is violated the InvalidOperation
        flag is raised.

        The result of pow(self, other, modulo) is identical to the
        result that would be obtained by computing (self**other) %
        modulo with unbounded precision, but is computed more
        efficiently.  It is always exact.
        """

        if modulo is not None:
            return self._power_modulo(other, modulo, context)

        other = _convert_other(other)
        if other is NotImplemented:
            return other

        if context is None:
            context = getcontext()

        # either argument is a NaN => result is NaN
        ans = self._check_nans(other, context)
        if ans:
            return ans

        # 0**0 = NaN (!), x**0 = 1 for nonzero x (including +/-Infinity)
        if not other:
            if not self:
                return context._raise_error(InvalidOperation, '0 ** 0')
            else:
                return _One

        # result has sign 1 iff self._sign is 1 and other is an odd integer
        result_sign = 0
        if self._sign == 1:
            if other._isinteger():
                if not other._iseven():
                    result_sign = 1
            else:
                # -ve**noninteger = NaN
                # (-0)**noninteger = 0**noninteger
                if self:
                    return context._raise_error(InvalidOperation,
                        'x ** y with x negative and y not an integer')
            # negate self, without doing any unwanted rounding
            self = self.copy_negate()

        # 0**(+ve or Inf)= 0; 0**(-ve or -Inf) = Infinity
        if not self:
            if other._sign == 0:
                return _dec_from_triple(result_sign, '0', 0)
            else:
                return _SignedInfinity[result_sign]

        # Inf**(+ve or Inf) = Inf; Inf**(-ve or -Inf) = 0
        if self._isinfinity():
            if other._sign == 0:
                return _SignedInfinity[result_sign]
            else:
                return _dec_from_triple(result_sign, '0', 0)

        # 1**other = 1, but the choice of exponent and the flags
        # depend on the exponent of self, and on whether other is a
        # positive integer, a negative integer, or neither
        if self == _One:
            if other._isinteger():
                # exp = max(self._exp*max(int(other), 0),
                # 1-context.prec) but evaluating int(other) directly
                # is dangerous until we know other is small (other
                # could be 1e999999999)
                if other._sign == 1:
                    multiplier = 0
                elif other > context.prec:
                    multiplier = context.prec
                else:
                    multiplier = int(other)

                exp = self._exp * multiplier
                if exp < 1-context.prec:
                    exp = 1-context.prec
                    context._raise_error(Rounded)
            else:
                context._raise_error(Inexact)
                context._raise_error(Rounded)
                exp = 1-context.prec

            return _dec_from_triple(result_sign, '1'+'0'*-exp, exp)

        # compute adjusted exponent of self
        self_adj = self.adjusted()

        # self ** infinity is infinity if self > 1, 0 if self < 1
        # self ** -infinity is infinity if self < 1, 0 if self > 1
        if other._isinfinity():
            if (other._sign == 0) == (self_adj < 0):
                return _dec_from_triple(result_sign, '0', 0)
            else:
                return _SignedInfinity[result_sign]

        # from here on, the result always goes through the call
        # to _fix at the end of this function.
        ans = None
        exact = False

        # crude test to catch cases of extreme overflow/underflow.  If
        # log10(self)*other >= 10**bound and bound >= len(str(Emax))
        # then 10**bound >= 10**len(str(Emax)) >= Emax+1 and hence
        # self**other >= 10**(Emax+1), so overflow occurs.  The test
        # for underflow is similar.
        bound = self._log10_exp_bound() + other.adjusted()
        if (self_adj >= 0) == (other._sign == 0):
            # self > 1 and other +ve, or self < 1 and other -ve
            # possibility of overflow
            if bound >= len(str(context.Emax)):
                ans = _dec_from_triple(result_sign, '1', context.Emax+1)
        else:
            # self > 1 and other -ve, or self < 1 and other +ve
            # possibility of underflow to 0
            Etiny = context.Etiny()
            if bound >= len(str(-Etiny)):
                ans = _dec_from_triple(result_sign, '1', Etiny-1)

        # try for an exact result with precision +1
        if ans is None:
            ans = self._power_exact(other, context.prec + 1)
            if ans is not None:
                if result_sign == 1:
                    ans = _dec_from_triple(1, ans._int, ans._exp)
                exact = True

        # usual case: inexact result, x**y computed directly as exp(y*log(x))
        if ans is None:
            p = context.prec
            x = _WorkRep(self)
            xc, xe = x.int, x.exp
            y = _WorkRep(other)
            yc, ye = y.int, y.exp
            if y.sign == 1:
                yc = -yc

            # compute correctly rounded result:  start with precision +3,
            # then increase precision until result is unambiguously roundable
            extra = 3
            while True:
                coeff, exp = _dpower(xc, xe, yc, ye, p+extra)
                if coeff % (5*10**(len(str(coeff))-p-1)):
                    break
                extra += 3

            ans = _dec_from_triple(result_sign, str(coeff), exp)

        # unlike exp, ln and log10, the power function respects the
        # rounding mode; no need to switch to ROUND_HALF_EVEN here

        # There's a difficulty here when 'other' is not an integer and
        # the result is exact.  In this case, the specification
        # requires that the Inexact flag be raised (in spite of
        # exactness), but since the result is exact _fix won't do this
        # for us.  (Correspondingly, the Underflow signal should also
        # be raised for subnormal results.)  We can't directly raise
        # these signals either before or after calling _fix, since
        # that would violate the precedence for signals.  So we wrap
        # the ._fix call in a temporary context, and reraise
        # afterwards.
        if exact and not other._isinteger():
            # pad with zeros up to length context.prec+1 if necessary; this
            # ensures that the Rounded signal will be raised.
            if len(ans._int) <= context.prec:
                expdiff = context.prec + 1 - len(ans._int)
                ans = _dec_from_triple(ans._sign, ans._int+'0'*expdiff,
                                       ans._exp-expdiff)

            # create a copy of the current context, with cleared flags/traps
            newcontext = context.copy()
            newcontext.clear_flags()
            for exception in _signals:
                newcontext.traps[exception] = 0

            # round in the new context
            ans = ans._fix(newcontext)

            # raise Inexact, and if necessary, Underflow
            newcontext._raise_error(Inexact)
            if newcontext.flags[Subnormal]:
                newcontext._raise_error(Underflow)

            # propagate signals to the original context; _fix could
            # have raised any of Overflow, Underflow, Subnormal,
            # Inexact, Rounded, Clamped.  Overflow needs the correct
            # arguments.  Note that the order of the exceptions is
            # important here.
            if newcontext.flags[Overflow]:
                context._raise_error(Overflow, 'above Emax', ans._sign)
            for exception in Underflow, Subnormal, Inexact, Rounded, Clamped:
                if newcontext.flags[exception]:
                    context._raise_error(exception)

        else:
            ans = ans._fix(context)

        return ans