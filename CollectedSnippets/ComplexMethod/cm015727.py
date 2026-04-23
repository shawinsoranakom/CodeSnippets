def rAssertAlmostEqual(self, a, b, rel_err = 2e-15, abs_err = 5e-323,
                           msg=None):
        """Fail if the two floating-point numbers are not almost equal.

        Determine whether floating-point values a and b are equal to within
        a (small) rounding error.  The default values for rel_err and
        abs_err are chosen to be suitable for platforms where a float is
        represented by an IEEE 754 double.  They allow an error of between
        9 and 19 ulps.
        """

        # special values testing
        if math.isnan(a):
            if math.isnan(b):
                return
            self.fail(msg or '{!r} should be nan'.format(b))

        if math.isinf(a):
            if a == b:
                return
            self.fail(msg or 'finite result where infinity expected: '
                      'expected {!r}, got {!r}'.format(a, b))

        # if both a and b are zero, check whether they have the same sign
        # (in theory there are examples where it would be legitimate for a
        # and b to have opposite signs; in practice these hardly ever
        # occur).
        if not a and not b:
            if math.copysign(1., a) != math.copysign(1., b):
                self.fail(msg or 'zero has wrong sign: expected {!r}, '
                          'got {!r}'.format(a, b))

        # if a-b overflows, or b is infinite, return False.  Again, in
        # theory there are examples where a is within a few ulps of the
        # max representable float, and then b could legitimately be
        # infinite.  In practice these examples are rare.
        try:
            absolute_error = abs(b-a)
        except OverflowError:
            pass
        else:
            # test passes if either the absolute error or the relative
            # error is sufficiently small.  The defaults amount to an
            # error of between 9 ulps and 19 ulps on an IEEE-754 compliant
            # machine.
            if absolute_error <= max(abs_err, rel_err * abs(a)):
                return
        self.fail(msg or
                  '{!r} and {!r} are not sufficiently close'.format(a, b))