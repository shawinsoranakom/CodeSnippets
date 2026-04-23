def check_ulpdiff(self, exact, rounded):
        # current precision
        p = context.p.prec

        # Convert infinities to the largest representable number + 1.
        x = exact
        if exact.is_infinite():
            x = _dec_from_triple(exact._sign, '10', context.p.Emax)
        y = rounded
        if rounded.is_infinite():
            y = _dec_from_triple(rounded._sign, '10', context.p.Emax)

        # err = (rounded - exact) / ulp(rounded)
        self.maxctx.prec = p * 2
        t = self.maxctx.subtract(y, x)
        if context.c.flags[C.Clamped] or \
           context.c.flags[C.Underflow]:
            # The standard ulp does not work in Underflow territory.
            ulp = self.harrison_ulp(y)
        else:
            ulp = self.standard_ulp(y, p)
        # Error in ulps.
        err = self.maxctx.divide(t, ulp)

        dir = self.rounding_direction(x, context.p.rounding)
        if dir == 0:
            if P.Decimal("-0.6") < err < P.Decimal("0.6"):
                return True
        elif dir == 1: # directed, upwards
            if P.Decimal("-0.1") < err < P.Decimal("1.1"):
                return True
        elif dir == -1: # directed, downwards
            if P.Decimal("-1.1") < err < P.Decimal("0.1"):
                return True
        else: # ROUND_05UP
            if P.Decimal("-1.1") < err < P.Decimal("1.1"):
                return True

        print("ulp: %s  error: %s  exact: %s  c_rounded: %s"
              % (ulp, err, exact, rounded))
        return False