def _is_multiple_of(self, numerator: Expr, denominator: int) -> bool:
        """
        Structural divisibility check: returns True only if numerator is
        provably a multiple of denominator.  Recurses over sympy expression
        structure before falling back to statically_known_true.
        """
        # Rule 1 — concrete value
        if isinstance(numerator, (int, sympy.Integer)):
            return int(numerator) % denominator == 0

        # Rule 2 — product: any factor divisible → product divisible
        if isinstance(numerator, sympy.Mul):
            for factor in numerator.args:
                if self._is_multiple_of(factor, denominator):
                    return True
            # Also check if combined constant factors are divisible
            const = 1
            for factor in numerator.args:
                if isinstance(factor, (int, sympy.Integer)):
                    const *= int(factor)
            if const != 1 and const % denominator == 0:
                return True

        # Rule 3 — sum: all terms divisible → sum divisible
        if isinstance(numerator, sympy.Add):
            if all(self._is_multiple_of(term, denominator) for term in numerator.args):
                return True

        # Rule 4 — FloorDiv(a, b): if a is multiple of b*n
        if isinstance(numerator, FloorDiv):
            a, b = numerator.args
            if isinstance(b, (int, sympy.Integer)):
                if self._is_multiple_of(a, int(b) * denominator):
                    return True

        # Rule 5 — Mod(a, b): Mod(a,b) = a - b*floor(a/b), so if both a and b
        # are multiples of n, then Mod(a,b) is too.
        if isinstance(numerator, (Mod, sympy.Mod)):
            a, b = numerator.args
            if self._is_multiple_of(a, denominator) and self._is_multiple_of(
                b, denominator
            ):
                return True

        # Rule 6 — axiom fallback: ask ShapeEnv
        expr = sympy.Eq(Mod(numerator, denominator), 0)
        return self.statically_known_true(expr)