def sqrt(self, context=None):
        """Return the square root of self."""
        if context is None:
            context = getcontext()

        if self._is_special:
            ans = self._check_nans(context=context)
            if ans:
                return ans

            if self._isinfinity() and self._sign == 0:
                return Decimal(self)

        if not self:
            # exponent = self._exp // 2.  sqrt(-0) = -0
            ans = _dec_from_triple(self._sign, '0', self._exp // 2)
            return ans._fix(context)

        if self._sign == 1:
            return context._raise_error(InvalidOperation, 'sqrt(-x), x > 0')

        # At this point self represents a positive number.  Let p be
        # the desired precision and express self in the form c*100**e
        # with c a positive real number and e an integer, c and e
        # being chosen so that 100**(p-1) <= c < 100**p.  Then the
        # (exact) square root of self is sqrt(c)*10**e, and 10**(p-1)
        # <= sqrt(c) < 10**p, so the closest representable Decimal at
        # precision p is n*10**e where n = round_half_even(sqrt(c)),
        # the closest integer to sqrt(c) with the even integer chosen
        # in the case of a tie.
        #
        # To ensure correct rounding in all cases, we use the
        # following trick: we compute the square root to an extra
        # place (precision p+1 instead of precision p), rounding down.
        # Then, if the result is inexact and its last digit is 0 or 5,
        # we increase the last digit to 1 or 6 respectively; if it's
        # exact we leave the last digit alone.  Now the final round to
        # p places (or fewer in the case of underflow) will round
        # correctly and raise the appropriate flags.

        # use an extra digit of precision
        prec = context.prec+1

        # write argument in the form c*100**e where e = self._exp//2
        # is the 'ideal' exponent, to be used if the square root is
        # exactly representable.  l is the number of 'digits' of c in
        # base 100, so that 100**(l-1) <= c < 100**l.
        op = _WorkRep(self)
        e = op.exp >> 1
        if op.exp & 1:
            c = op.int * 10
            l = (len(self._int) >> 1) + 1
        else:
            c = op.int
            l = len(self._int)+1 >> 1

        # rescale so that c has exactly prec base 100 'digits'
        shift = prec-l
        if shift >= 0:
            c *= 100**shift
            exact = True
        else:
            c, remainder = divmod(c, 100**-shift)
            exact = not remainder
        e -= shift

        # find n = floor(sqrt(c)) using Newton's method
        n = 10**prec
        while True:
            q = c//n
            if n <= q:
                break
            else:
                n = n + q >> 1
        exact = exact and n*n == c

        if exact:
            # result is exact; rescale to use ideal exponent e
            if shift >= 0:
                # assert n % 10**shift == 0
                n //= 10**shift
            else:
                n *= 10**-shift
            e += shift
        else:
            # result is not exact; fix last digit as described above
            if n % 5 == 0:
                n += 1

        ans = _dec_from_triple(0, str(n), e)

        # round, and fit to current context
        context = context._shallow_copy()
        rounding = context._set_rounding(ROUND_HALF_EVEN)
        ans = ans._fix(context)
        context.rounding = rounding

        return ans