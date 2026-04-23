def _do_test2(self, fn, inp1, inp2, shape_env, is_unary_fn):
        # Helper function
        # NB: don't use one as that will get specialized
        # TODO: We don't have to circuitously create the float, can just
        # create a symfloat directly
        seed_node = (create_symint(shape_env, 2) / 2.0).node
        bool_seed_node = (create_symint(shape_env, 2) == 2).node

        def get_sym_inp(inp):
            # NB: this must come before int
            if isinstance(inp, bool):
                return torch.SymBool(to_node(bool_seed_node, inp))
            elif isinstance(inp, int):
                return torch.SymInt(to_node(seed_node, inp))
            else:
                return torch.SymFloat(to_node(seed_node, inp))

        if fn == "float_pow":
            if inp1 < 0:
                return

        if fn == "pow_by_natural":
            if isinstance(inp1, float) or isinstance(inp2, float):
                return
            if inp2 < 0:
                return

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

        lambda_apply = method_to_operator(fn)

        def guard_fn(v):
            if type(v) in (SymBool, bool):
                return guard_bool(v)
            elif type(v) in (SymFloat, float):
                return guard_float(v)
            else:  # SymInt, int
                return guard_int(v)

        # Get reference result
        with maybe_xfail(inp1, inp2):
            if is_unary_fn:
                ref_out = lambda_apply(inp1)
            else:
                ref_out = lambda_apply(inp1, inp2)

        # Symified first arg
        sym_inp1 = get_sym_inp(inp1)
        with maybe_xfail(sym_inp1, inp2):
            if is_unary_fn:
                out = lambda_apply(sym_inp1)
            else:
                out = lambda_apply(sym_inp1, inp2)
            self.assertTrue(isinstance(out, (SymInt, SymFloat, SymBool)))
            out = guard_fn(out)
            self.assertEqual(out, ref_out)

        if is_unary_fn:
            return

        # Symified second arg
        sym_inp2 = get_sym_inp(inp2)
        with maybe_xfail(inp1, sym_inp2):
            out = lambda_apply(inp1, sym_inp2)
            self.assertTrue(isinstance(out, (SymInt, SymFloat, SymBool)))
            out = guard_fn(out)
            self.assertEqual(out, ref_out)

        # Symified both args
        with maybe_xfail(sym_inp1, sym_inp2):
            out = lambda_apply(sym_inp1, sym_inp2)
            self.assertTrue(isinstance(out, (SymInt, SymFloat, SymBool)))
            out = guard_fn(out)
            self.assertEqual(out, ref_out)