def maybe_xfail(inp1, inp2):
            if fn == "sym_sqrt" and inp1 < 0:
                # ValueError: math domain error
                return self.assertRaises((ValueError,))
            elif (
                fn in ("float_truediv", "int_truediv", "int_floordiv", "mod")
                and inp2 == 0
            ):
                # ZeroDivisionError: division by zero
                return self.assertRaises((ZeroDivisionError,))
            elif fn in ["float_pow", "pow_by_natural"] and inp1 == 0 and inp2 < 0:
                # ZeroDivisionError: 0.0 cannot be raised to a negative power
                return self.assertRaises((ZeroDivisionError,))
            elif (
                # TODO: dear catastrophe waitress,
                # this doesn't work
                fn in ["float_pow", "pow_by_natural"]
                and inp1 < 0
                and (
                    type(inp1) is (SymInt, SymFloat) or type(inp2) is (SymInt, SymFloat)
                )
                and (type(inp1) is (SymFloat, float) or type(inp2) is (SymFloat, float))
            ):
                # Complex result, which we do not support:
                # TypeError: Cannot convert complex to float
                return self.assertRaises((RuntimeError,))
            elif fn in ("lshift", "rshift") and not (
                isinstance(inp1, (SymInt, int)) and isinstance(inp2, (SymInt, int))
            ):
                # TypeError: unsupported operand type(s)
                return self.assertRaises((TypeError,))
            elif fn in ("lshift", "rshift") and inp2 < 0:
                # ValueError: math domain error
                return self.assertRaises((ValueError,))
            else:
                return contextlib.nullcontext()