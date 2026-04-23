def _power_exact(self, other, p):
        """Attempt to compute self**other exactly.

        Given Decimals self and other and an integer p, attempt to
        compute an exact result for the power self**other, with p
        digits of precision.  Return None if self**other is not
        exactly representable in p digits.

        Assumes that elimination of special cases has already been
        performed: self and other must both be nonspecial; self must
        be positive and not numerically equal to 1; other must be
        nonzero.  For efficiency, other._exp should not be too large,
        so that 10**abs(other._exp) is a feasible calculation."""

        # In the comments below, we write x for the value of self and y for the
        # value of other.  Write x = xc*10**xe and abs(y) = yc*10**ye, with xc
        # and yc positive integers not divisible by 10.

        # The main purpose of this method is to identify the *failure*
        # of x**y to be exactly representable with as little effort as
        # possible.  So we look for cheap and easy tests that
        # eliminate the possibility of x**y being exact.  Only if all
        # these tests are passed do we go on to actually compute x**y.

        # Here's the main idea.  Express y as a rational number m/n, with m and
        # n relatively prime and n>0.  Then for x**y to be exactly
        # representable (at *any* precision), xc must be the nth power of a
        # positive integer and xe must be divisible by n.  If y is negative
        # then additionally xc must be a power of either 2 or 5, hence a power
        # of 2**n or 5**n.
        #
        # There's a limit to how small |y| can be: if y=m/n as above
        # then:
        #
        #  (1) if xc != 1 then for the result to be representable we
        #      need xc**(1/n) >= 2, and hence also xc**|y| >= 2.  So
        #      if |y| <= 1/nbits(xc) then xc < 2**nbits(xc) <=
        #      2**(1/|y|), hence xc**|y| < 2 and the result is not
        #      representable.
        #
        #  (2) if xe != 0, |xe|*(1/n) >= 1, so |xe|*|y| >= 1.  Hence if
        #      |y| < 1/|xe| then the result is not representable.
        #
        # Note that since x is not equal to 1, at least one of (1) and
        # (2) must apply.  Now |y| < 1/nbits(xc) iff |yc|*nbits(xc) <
        # 10**-ye iff len(str(|yc|*nbits(xc)) <= -ye.
        #
        # There's also a limit to how large y can be, at least if it's
        # positive: the normalized result will have coefficient xc**y,
        # so if it's representable then xc**y < 10**p, and y <
        # p/log10(xc).  Hence if y*log10(xc) >= p then the result is
        # not exactly representable.

        # if len(str(abs(yc*xe)) <= -ye then abs(yc*xe) < 10**-ye,
        # so |y| < 1/xe and the result is not representable.
        # Similarly, len(str(abs(yc)*xc_bits)) <= -ye implies |y|
        # < 1/nbits(xc).

        x = _WorkRep(self)
        xc, xe = x.int, x.exp
        while xc % 10 == 0:
            xc //= 10
            xe += 1

        y = _WorkRep(other)
        yc, ye = y.int, y.exp
        while yc % 10 == 0:
            yc //= 10
            ye += 1

        # case where xc == 1: result is 10**(xe*y), with xe*y
        # required to be an integer
        if xc == 1:
            xe *= yc
            # result is now 10**(xe * 10**ye);  xe * 10**ye must be integral
            while xe % 10 == 0:
                xe //= 10
                ye += 1
            if ye < 0:
                return None
            exponent = xe * 10**ye
            if y.sign == 1:
                exponent = -exponent
            # if other is a nonnegative integer, use ideal exponent
            if other._isinteger() and other._sign == 0:
                ideal_exponent = self._exp*int(other)
                zeros = min(exponent-ideal_exponent, p-1)
            else:
                zeros = 0
            return _dec_from_triple(0, '1' + '0'*zeros, exponent-zeros)

        # case where y is negative: xc must be either a power
        # of 2 or a power of 5.
        if y.sign == 1:
            last_digit = xc % 10
            if last_digit in (2,4,6,8):
                # quick test for power of 2
                if xc & -xc != xc:
                    return None
                # now xc is a power of 2; e is its exponent
                e = _nbits(xc)-1

                # We now have:
                #
                #   x = 2**e * 10**xe, e > 0, and y < 0.
                #
                # The exact result is:
                #
                #   x**y = 5**(-e*y) * 10**(e*y + xe*y)
                #
                # provided that both e*y and xe*y are integers.  Note that if
                # 5**(-e*y) >= 10**p, then the result can't be expressed
                # exactly with p digits of precision.
                #
                # Using the above, we can guard against large values of ye.
                # 93/65 is an upper bound for log(10)/log(5), so if
                #
                #   ye >= len(str(93*p//65))
                #
                # then
                #
                #   -e*y >= -y >= 10**ye > 93*p/65 > p*log(10)/log(5),
                #
                # so 5**(-e*y) >= 10**p, and the coefficient of the result
                # can't be expressed in p digits.

                # emax >= largest e such that 5**e < 10**p.
                emax = p*93//65
                if ye >= len(str(emax)):
                    return None

                # Find -e*y and -xe*y; both must be integers
                e = _decimal_lshift_exact(e * yc, ye)
                xe = _decimal_lshift_exact(xe * yc, ye)
                if e is None or xe is None:
                    return None

                if e > emax:
                    return None
                xc = 5**e

            elif last_digit == 5:
                # e >= log_5(xc) if xc is a power of 5; we have
                # equality all the way up to xc=5**2658
                e = _nbits(xc)*28//65
                xc, remainder = divmod(5**e, xc)
                if remainder:
                    return None
                while xc % 5 == 0:
                    xc //= 5
                    e -= 1

                # Guard against large values of ye, using the same logic as in
                # the 'xc is a power of 2' branch.  10/3 is an upper bound for
                # log(10)/log(2).
                emax = p*10//3
                if ye >= len(str(emax)):
                    return None

                e = _decimal_lshift_exact(e * yc, ye)
                xe = _decimal_lshift_exact(xe * yc, ye)
                if e is None or xe is None:
                    return None

                if e > emax:
                    return None
                xc = 2**e
            else:
                return None

            # An exact power of 10 is representable, but can convert to a
            # string of any length. But an exact power of 10 shouldn't be
            # possible at this point.
            assert xc > 1, self
            assert xc % 10 != 0, self
            strxc = str(xc)
            if len(strxc) > p:
                return None
            xe = -e-xe
            return _dec_from_triple(0, strxc, xe)

        # now y is positive; find m and n such that y = m/n
        if ye >= 0:
            m, n = yc*10**ye, 1
        else:
            if xe != 0 and len(str(abs(yc*xe))) <= -ye:
                return None
            xc_bits = _nbits(xc)
            if len(str(abs(yc)*xc_bits)) <= -ye:
                return None
            m, n = yc, 10**(-ye)
            while m % 2 == n % 2 == 0:
                m //= 2
                n //= 2
            while m % 5 == n % 5 == 0:
                m //= 5
                n //= 5

        # compute nth root of xc*10**xe
        if n > 1:
            # if 1 < xc < 2**n then xc isn't an nth power
            if xc_bits <= n:
                return None

            xe, rem = divmod(xe, n)
            if rem != 0:
                return None

            # compute nth root of xc using Newton's method
            a = 1 << -(-_nbits(xc)//n) # initial estimate
            while True:
                q, r = divmod(xc, a**(n-1))
                if a <= q:
                    break
                else:
                    a = (a*(n-1) + q)//n
            if not (a == q and r == 0):
                return None
            xc = a

        # now xc*10**xe is the nth root of the original xc*10**xe
        # compute mth power of xc*10**xe

        # if m > p*100//_log10_lb(xc) then m > p/log10(xc), hence xc**m >
        # 10**p and the result is not representable.
        if xc > 1 and m > p*100//_log10_lb(xc):
            return None
        xc = xc**m
        xe *= m
        # An exact power of 10 is representable, but can convert to a string
        # of any length. But an exact power of 10 shouldn't be possible at
        # this point.
        assert xc > 1, self
        assert xc % 10 != 0, self
        str_xc = str(xc)
        if len(str_xc) > p:
            return None

        # by this point the result *is* exactly representable
        # adjust the exponent to get as close as possible to the ideal
        # exponent, if necessary
        if other._isinteger() and other._sign == 0:
            ideal_exponent = self._exp*int(other)
            zeros = min(xe-ideal_exponent, p-len(str_xc))
        else:
            zeros = 0
        return _dec_from_triple(0, str_xc+'0'*zeros, xe-zeros)