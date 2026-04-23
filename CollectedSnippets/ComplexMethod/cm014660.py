def default_val_str(val):
                if isinstance(val, (tuple, list)):
                    str_pieces = ["(" if isinstance(val, tuple) else "["]
                    str_pieces.append(", ".join(default_val_str(v) for v in val))
                    if isinstance(val, tuple) and len(str_pieces) == 2:
                        str_pieces.append(",")
                    str_pieces.append(")" if isinstance(val, tuple) else "]")
                    return "".join(str_pieces)

                # Need to fix up some default value strings.
                # First case: modules. Default module `repr` contains the FS path of the module.
                # Don't leak that
                if isinstance(val, types.ModuleType):
                    return f"<module {val.__name__}>"

                # Second case: callables. Callables (such as lambdas) encode their address in
                # their string repr. Don't do that
                if callable(val):
                    return f"<function {val.__name__}>"

                return str(val)