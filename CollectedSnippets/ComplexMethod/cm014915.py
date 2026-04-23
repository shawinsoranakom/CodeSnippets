def test_math_ops(self):
        def checkMathWrap(func_name, num_args=1, is_float=True, **args):
            if is_float:
                checkMath(func_name, num_args, True, **args)
                checkMath(func_name, num_args, False, **args)
            else:
                checkMath(func_name, num_args, is_float, **args)

        inf = float("inf")
        NaN = float("nan")
        mx_int = 2**31 - 1
        mn_int = -2**31
        float_vals = ([inf, NaN, 0.0, 1.0, 2.2, -1.0, -0.0, -2.2, -inf, 1, 0, 2] +
                      [10.0 ** i for i in range(5)] + [-(10.0 ** i) for i in range(5)])
        int_vals = list(range(-5, 5, 1)) + [mx_int + 5, mx_int * 2, mn_int - 5, mn_int * 2]

        def checkMath(func_name, num_args, is_float=True, ret_type="float", debug=False, vals=None, args_type=None):
            funcs_template = dedent('''
            def func(a, b):
                # type: {args_type} -> {ret_type}
                return math.{func}({args})
            ''')
            if num_args == 1:
                args = "a"
            elif num_args == 2:
                args = "a, b"
            else:
                raise RuntimeError("Test doesn't support more than 2 arguments")
            if args_type is None:
                args_type = "(float, float)" if is_float else "(int, int)"
            funcs_str = funcs_template.format(func=func_name, args=args, args_type=args_type, ret_type=ret_type)
            scope = {}
            execWrapper(funcs_str, globals(), scope)
            cu = torch.jit.CompilationUnit(funcs_str)
            f_script = cu.func
            f = scope['func']

            if vals is None:
                vals = float_vals if is_float else int_vals
                vals = [(i, j) for i in vals for j in vals]

            for a, b in vals:
                res_python = None
                res_script = None
                try:
                    res_python = f(a, b)
                except Exception as e:
                    res_python = e
                try:
                    res_script = f_script(a, b)
                except Exception as e:
                    res_script = e
                if debug:
                    print("in: ", a, b)
                    print("out: ", res_python, res_script)
                # We can't use assertEqual because of a couple of differences:
                # 1. nan == nan should return true
                # 2. When python functions throw an exception, we usually want to silently ignore them.
                # (ie: We want to return `nan` for math.sqrt(-5))
                if res_python != res_script:
                    if isinstance(res_python, Exception):
                        continue

                    if type(res_python) is type(res_script):
                        if isinstance(res_python, tuple) and (math.isnan(res_python[0]) == math.isnan(res_script[0])):
                            continue
                        if isinstance(res_python, float) and math.isnan(res_python) and math.isnan(res_script):
                            continue
                    msg = (f"Failed on {func_name} with inputs {a} {b}. Python: {res_python}, Script: {res_script}")
                    # math.pow() behavior has changed in 3.11, see https://docs.python.org/3/library/math.html#math.pow
                    if sys.version_info >= (3, 11) and func_name == "pow" and a == 0.0 and b == -math.inf:
                        self.assertTrue(res_python == math.inf and type(res_script) is RuntimeError)
                    else:
                        self.assertEqual(res_python, res_script, msg=msg, atol=(1e-4) * max(abs(res_python), res_script), rtol=0)

        unary_float_ops = ["log", "log1p", "log10", "exp", "sqrt", "gamma", "lgamma", "erf",
                           "erfc", "expm1", "fabs", "acos", "asin", "atan", "cos", "sin", "tan",
                           "asinh", "atanh", "acosh", "sinh", "cosh", "tanh", "degrees", "radians"]
        binary_float_ops = ["atan2", "fmod", "copysign"]
        for op in unary_float_ops:
            checkMathWrap(op, 1)
        for op in binary_float_ops:
            checkMathWrap(op, 2)

        checkMath("modf", 1, ret_type="Tuple[float, float]")
        checkMath("frexp", 1, ret_type="Tuple[float, int]")
        checkMath("isnan", 1, ret_type="bool")
        checkMath("isinf", 1, ret_type="bool")
        checkMath("ldexp", 2, is_float=False, ret_type="float", args_type="(float, int)",
                  vals=[(i, j) for i in float_vals for j in range(-10, 10)])
        checkMath("pow", 2, is_float=False, ret_type="float")
        checkMath("pow", 2, is_float=True, ret_type="float")
        checkMathWrap("floor", ret_type="int")
        checkMathWrap("ceil", ret_type="int")
        checkMathWrap("gcd", 2, is_float=False, ret_type="int")
        checkMath("isfinite", 1, ret_type="bool")
        checkMathWrap("remainder", 2)
        checkMathWrap("factorial", 1, is_float=False, ret_type="int", vals=[(i, 0) for i in range(-2, 10)])