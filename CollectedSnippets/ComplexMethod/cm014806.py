def test_python_interp_fx(self, fn):
        # These never show up from symbolic_shapes
        if fn in ("log", "exp"):
            return

        # Sympy does not support truncation on symbolic shapes
        if fn in ("truncdiv", "mod"):
            return

        vals = CONSTANTS
        if fn in {*UNARY_BOOL_OPS, *BINARY_BOOL_OPS}:
            vals = [True, False]
        elif fn in BITWISE_OPS:
            vals = vals + [True, False]

        arity = 1
        if fn in {*BINARY_OPS, *BINARY_BOOL_OPS, *COMPARE_OPS}:
            arity = 2

        is_integer = None
        if fn == "pow_by_natural":
            is_integer = True

        x = sympy.Dummy("x", integer=is_integer)
        y = sympy.Dummy("y", integer=is_integer)

        symbols = [x]
        if arity == 2:
            symbols = [x, y]

        for args in itertools.product(vals, repeat=arity):
            if arity == 1 and not valid_unary(fn, *args):
                continue
            elif arity == 2 and not valid_binary(fn, *args):
                continue
            if fn == "truncdiv" and args[1] == 0:
                continue
            elif fn in ("pow", "pow_by_natural") and (args[0] == 0 and args[1] <= 0):
                continue
            elif fn == "floordiv" and args[1] == 0:
                continue
            with self.subTest(args=args):
                # Workaround mpf from symbol error
                if fn == "minimum":
                    sympy_expr = sympy.Min(x, y)
                elif fn == "maximum":
                    sympy_expr = sympy.Max(x, y)
                else:
                    sympy_expr = getattr(ReferenceAnalysis, fn)(*symbols)

                if arity == 1:

                    def trace_f(px):
                        return sympy_interp(
                            PythonReferenceAnalysis, {x: px}, sympy_expr
                        )

                else:

                    def trace_f(px, py):
                        return sympy_interp(
                            PythonReferenceAnalysis, {x: px, y: py}, sympy_expr
                        )

                gm = fx.symbolic_trace(trace_f)

                self.assertEqual(
                    sympy_interp(
                        PythonReferenceAnalysis, dict(zip(symbols, args)), sympy_expr
                    ),
                    gm(*args),
                )