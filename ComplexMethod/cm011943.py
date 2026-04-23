def evaluate_min(self, left: Expr, right: Expr) -> Expr:
        """Return the smaller of left and right, and guard on that choice."""
        if isinstance(left, Expr):
            left = sympy_subs(left, self.inv_precomputed_replacements)  # type: ignore[arg-type]
        if isinstance(right, Expr):
            right = sympy_subs(right, self.inv_precomputed_replacements)  # type: ignore[arg-type]
        if self.guard_or_false(sympy.Le(left, right)):
            return left
        if self.guard_or_false(sympy.Le(right, left)):
            return right

        # GCD fallback: if gcd(a, b) == a then a divides b, implying a <= b.
        #
        # TODO: This is NOT always sound for unbacked symints.  It can
        # produce wrong results when:
        #   - inputs can be negative: gcd(u0, 10*u0) = u0, returns u0,
        #     but if u0 < 0 then u0 > 10*u0 (e.g. u0=-1: min(-1,-10) = -10)
        #   - a factor can be zero: gcd(u0, u0*u1) = u0, returns u0,
        #     but if u1=0 then u0*u1=0 < u0 (e.g. u0=5,u1=0: min(5,0) = 0)
        # TODO shall we add a runtime assertion at least.
        gcd = sympy.gcd(left, right)
        if left == gcd:
            return left
        if right == gcd:
            return right

        # Min/Max fallback: we can prove Min(a, b) <= c when any arg <= c, but
        # sympy doesn't simplify this yet. So, evaluate it here. Same for Max.
        for lhs, rhs in [(left, right), (right, left)]:

            def le_rhs(a: Expr) -> bool:
                return self.guard_or_false(sympy.Le(a, rhs))

            # Min(Min(a, b), c) ==> Min(a, b) if (a <= c) or (b <= c).
            if isinstance(lhs, sympy.Min) and any(le_rhs(a) for a in lhs.args):
                return lhs
            # Min(Max(a, b), c) ==> Max(a, b) if (a <= c) and (b <= c).
            if isinstance(lhs, sympy.Max) and all(le_rhs(a) for a in lhs.args):
                return lhs

        raise TypeError(
            f"evaluate_min({left}, {right}) with unbacked symints"
        ) from None