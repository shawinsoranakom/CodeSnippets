def eval(
        cls, base: sympy.Integer, divisor: sympy.Integer, modulus: sympy.Integer
    ) -> sympy.Basic | None:
        if base == 0 or modulus == 1:
            return sympy.S.Zero
        if (
            isinstance(base, sympy.Integer)
            and isinstance(divisor, sympy.Integer)
            and isinstance(modulus, sympy.Integer)
        ):
            return (base // divisor) % modulus

        try:
            if divisor != 1:
                gcd = sympy.gcd(base, divisor)
                if gcd != 1:
                    return ModularIndexing(
                        sympy.simplify(base / gcd),
                        sympy.simplify(divisor / gcd),
                        modulus,
                    )
        except sympy.PolynomialError:
            pass  # https://github.com/pytorch/pytorch/issues/108276

        if isinstance(base, sympy.Add):
            new_terms: list[sympy.Integer] = []
            all_positive: bool = True
            for term in base.args:
                if sympy.gcd(term, modulus * divisor) != modulus * divisor:
                    if (isinstance(term, sympy.Integer) and term < 0) or (
                        isinstance(term, sympy.Mul)
                        and isinstance(term.args[0], sympy.Integer)
                        and term.args[0] < 0
                    ):
                        # workaround for https://github.com/triton-lang/triton/issues/619,
                        # if there are negative terms, // produces wrong result
                        # TODO if https://github.com/triton-lang/triton/issues/619 is fixed
                        # this optimization would become valid
                        all_positive = False
                        break
                    else:
                        new_terms.append(term)

            if len(new_terms) != len(base.args) and all_positive:
                return ModularIndexing(sum(new_terms), divisor, modulus)

        if isinstance(base, FloorDiv):
            return ModularIndexing(base.args[0], base.args[1] * divisor, modulus)

        return None