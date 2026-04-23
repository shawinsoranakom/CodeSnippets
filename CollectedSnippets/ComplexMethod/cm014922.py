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