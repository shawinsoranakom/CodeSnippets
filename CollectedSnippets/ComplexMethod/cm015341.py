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