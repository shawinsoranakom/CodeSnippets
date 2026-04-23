def bind_symint(arg: object, val: object) -> None:
            if isinstance(val, SymInt):
                if not isinstance(arg, int):
                    raise AssertionError(f"Expected int, got {type(arg)}")
                s = val.node.expr

                if isinstance(s, sympy.Symbol):
                    if s in bindings:
                        if bindings[s] != arg:
                            raise AssertionError(f"{bindings[s]} != {arg}")
                    else:
                        bindings[s] = arg
                elif isinstance(-s, sympy.Symbol):
                    if -s in bindings:
                        if bindings[-s] != -arg:
                            raise AssertionError(f"{bindings[-s]} != {-arg}")
                    else:
                        bindings[-s] = -arg