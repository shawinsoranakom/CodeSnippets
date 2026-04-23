def test_interp(self, fn):
        # SymPy does not implement truncation for Expressions
        if fn in ("div", "truncdiv", "minimum", "maximum", "mod"):
            return

        is_integer = None
        if fn == "pow_by_natural":
            is_integer = True

        x = sympy.Dummy("x", integer=is_integer)
        y = sympy.Dummy("y", integer=is_integer)

        vals = CONSTANTS
        if fn in {*UNARY_BOOL_OPS, *BINARY_BOOL_OPS}:
            vals = [True, False]
        elif fn in BITWISE_OPS:
            vals = vals + [True, False]
        arity = 1
        if fn in {*BINARY_OPS, *BINARY_BOOL_OPS, *COMPARE_OPS}:
            arity = 2
        symbols = [x]
        if arity == 2:
            symbols = [x, y]
        for args in itertools.product(vals, repeat=arity):
            if arity == 1 and not valid_unary(fn, *args):
                continue
            elif arity == 2 and not valid_binary(fn, *args):
                continue
            with self.subTest(args=args):
                sargs = [sympy.sympify(a) for a in args]
                sympy_expr = getattr(ReferenceAnalysis, fn)(*symbols)
                ref_r = getattr(ReferenceAnalysis, fn)(*sargs)
                # Yes, I know this is a long-winded way of saying xreplace; the
                # point is to test sympy_interp
                r = sympy_interp(
                    ReferenceAnalysis, dict(zip(symbols, sargs)), sympy_expr
                )
                self.assertEqual(ref_r, r)