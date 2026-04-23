def eval(cls, p: sympy.Expr, q: sympy.Expr) -> sympy.Expr | None:
        # python test/dynamo/test_export.py -k ExportTests.test_trivial_constraint
        # Triggered by sympy.solvers.inequalities.reduce_inequalities
        # assert p.is_integer, p
        # assert q.is_integer, q

        if q.is_zero:
            raise ZeroDivisionError("Modulo by zero")

        # Three cases:
        #   1. p == 0
        #   2. p is either q or -q
        #   3. p is integer and q == 1
        if p is S.Zero or p in (q, -q) or q == 1:
            return S.Zero

        # Evaluate if they are both literals.
        if q.is_Number and p.is_Number:
            return p % q

        # If q == 2, it's a matter of whether p is odd or even.
        if q.is_Number and q == 2:
            if p.is_even:
                return S.Zero
            if p.is_odd:
                return S.One

        # If p is a multiple of q.
        r = p / q
        if r.is_integer:
            return S.Zero

        # If p < q and its ratio is positive, then:
        #   - floor(p / q) = 0
        #   - p % q = p - floor(p / q) * q = p
        less = p < q
        # pyrefly: ignore [missing-attribute]
        if less.is_Boolean and bool(less) and r.is_positive:
            return p

        if sympy.Mod(p, q) == 0:
            return S.Zero

        return None