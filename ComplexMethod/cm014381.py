def eval(cls, base: sympy.Integer, divisor: sympy.Integer) -> sympy.Basic | None:
        # python test/test_dynamic_shapes.py -k TestDimConstraints.test_dim_constraints_solve_full
        # Assert triggered by inequality solver
        # assert base.is_integer, base
        # assert divisor.is_integer, divisor

        # We don't provide the same error message as in Python because SymPy
        # makes it difficult to check the types.
        if divisor.is_zero:
            raise ZeroDivisionError("division by zero")
        if is_infinite(base) and is_infinite(divisor):
            return sympy.nan
        if base is sympy.nan or divisor is sympy.nan:
            return sympy.nan

        if base.is_zero:
            return sympy.S.Zero
        if base.is_integer and equal_valued(divisor, 1):
            return base
        if base.is_integer and equal_valued(divisor, -1):
            return sympy.Mul(base, -1)
        if base == divisor:
            return sympy.S.One

        if (
            isinstance(base, sympy.Number)
            and isinstance(divisor, sympy.Number)
            and (is_infinite(base) or is_infinite(divisor))
        ):
            r = float(base) / float(divisor)
            if r == math.inf:
                return int_oo
            elif r == -math.inf:
                return -int_oo
            elif math.isnan(r):
                return sympy.nan
            else:
                return sympy.Integer(math.floor(r))
        if isinstance(base, sympy.Integer) and isinstance(divisor, sympy.Integer):
            return sympy.Integer(int(base) // int(divisor))
        if isinstance(base, FloorDiv):
            return FloorDiv(base.args[0], base.args[1] * divisor)

        # Expands (x + y) // b into x // b + y // b.
        # This only works if floor is an identity, i.e. x / b is an integer.
        if isinstance(divisor, sympy.Integer):
            quotients = 0
            terms = []
            for term in sympy.Add.make_args(base):
                quotient = term / divisor

                # This is a sympy bug fixed in https://github.com/sympy/sympy/pull/28442
                # sympy can generate a quotient with (1/22)*.... such that quotient.is_integer is True
                # FloorDiv should not allow that as output. see
                quotient_is_integer = None
                if isinstance(quotient, sympy.Mul) and TorchVersion(
                    sympy.__version__
                ) < TorchVersion("1.15.0"):
                    rationals = quotient.atoms(sympy.Rational)
                    all_rationals_ints = all(r.q == 1 for r in rationals)
                    quotient_is_integer = quotient.is_integer and all_rationals_ints
                else:
                    quotient_is_integer = quotient.is_integer

                if quotient_is_integer:
                    terms.append(term)
                    quotients += quotient

            if len(terms) != 0:
                # Passing evaluate = False since expression will be optimized during the subtraction post its construction.
                return (
                    FloorDiv(base - sympy.Add(*terms, evaluate=False), divisor)
                    + quotients
                )

        try:
            gcd = simple_floordiv_gcd(base, divisor)
            if equal_valued(gcd, 1) and isinstance(divisor, sympy.Add):
                gcd = sympy.gcd(base, divisor)
            if not equal_valued(gcd, 1):
                return FloorDiv(
                    sympy.simplify(base / gcd), sympy.simplify(divisor / gcd)
                )
        except sympy.PolynomialError:
            pass  # https://github.com/pytorch/pytorch/issues/108276

        return None