def test_complex_constants_and_ops(self):
        vals = (
            [0.0, 1.0, 2.2, -1.0, -0.0, -2.2, 1, 0, 2]
            + [10.0**i for i in range(2)]
            + [-(10.0**i) for i in range(2)]
        )
        complex_vals = tuple(complex(x, y) for x, y in product(vals, vals))

        funcs_template = dedent(
            """
            def func(a: complex):
                return cmath.{func_or_const}(a)
            """
        )

        def checkCmath(func_name, funcs_template=funcs_template):
            funcs_str = funcs_template.format(func_or_const=func_name)
            scope = {}
            execWrapper(funcs_str, globals(), scope)
            cu = torch.jit.CompilationUnit(funcs_str)
            f_script = cu.func
            f = scope["func"]

            if func_name in ["isinf", "isnan", "isfinite"]:
                new_vals = vals + ([float("inf"), float("nan"), -1 * float("inf")])
                final_vals = tuple(
                    complex(x, y) for x, y in product(new_vals, new_vals)
                )
            else:
                final_vals = complex_vals

            for a in final_vals:
                res_python = None
                res_script = None
                try:
                    res_python = f(a)
                except Exception as e:
                    res_python = e
                try:
                    res_script = f_script(a)
                except Exception as e:
                    res_script = e

                if res_python != res_script:
                    if isinstance(res_python, Exception):
                        continue

                    msg = f"Failed on {func_name} with input {a}. Python: {res_python}, Script: {res_script}"
                    self.assertEqual(res_python, res_script, msg=msg)

        unary_ops = [
            "log",
            "log10",
            "sqrt",
            "exp",
            "sin",
            "cos",
            "asin",
            "acos",
            "atan",
            "sinh",
            "cosh",
            "tanh",
            "asinh",
            "acosh",
            "atanh",
            "phase",
            "isinf",
            "isnan",
            "isfinite",
        ]

        # --- Unary ops ---
        for op in unary_ops:
            checkCmath(op)

        def fn(x: complex):
            return abs(x)

        for val in complex_vals:
            self.checkScript(fn, (val,))

        def pow_complex_float(x: complex, y: float):
            return pow(x, y)

        def pow_float_complex(x: float, y: complex):
            return pow(x, y)

        self.checkScript(pow_float_complex, (2, 3j))
        self.checkScript(pow_complex_float, (3j, 2))

        def pow_complex_complex(x: complex, y: complex):
            return pow(x, y)

        for x, y in zip(complex_vals, complex_vals):
            # Reference: https://github.com/pytorch/pytorch/issues/54622
            if x == 0:
                continue
            self.checkScript(pow_complex_complex, (x, y))

        if not IS_MACOS:
            # --- Binary op ---
            def rect_fn(x: float, y: float):
                return cmath.rect(x, y)

            for x, y in product(vals, vals):
                self.checkScript(
                    rect_fn,
                    (
                        x,
                        y,
                    ),
                )

        func_constants_template = dedent(
            """
            def func():
                return cmath.{func_or_const}
            """
        )
        float_consts = ["pi", "e", "tau", "inf", "nan"]
        complex_consts = ["infj", "nanj"]
        for x in float_consts + complex_consts:
            checkCmath(x, funcs_template=func_constants_template)