def test_tensor_interp(self, fn):
        # Skip operations not implemented or not applicable for tensors
        if fn in ("div", "truncdiv", "int_truediv", "mod", "round_decimal"):
            return

        is_integer = None
        if fn == "pow_by_natural":
            is_integer = True

        x = sympy.Symbol("x", integer=is_integer)
        y = sympy.Symbol("y", integer=is_integer)

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
                tensor_args = [
                    torch.tensor(
                        a, dtype=torch.double if isinstance(a, float) else torch.int64
                    )
                    for a in args
                ]

                try:
                    tensor_fn = getattr(TensorReferenceAnalysis, fn)
                    sympy_expr = getattr(ReferenceAnalysis, fn)(*symbols)
                    direct_result = tensor_fn(*tensor_args)
                    interp_result = sympy_interp(
                        TensorReferenceAnalysis,
                        dict(zip(symbols, tensor_args)),
                        sympy_expr,
                    )

                    # Ensure both results are of the same dtype for comparison
                    if direct_result.dtype != interp_result.dtype:
                        if (
                            direct_result.dtype == torch.bool
                            or interp_result.dtype == torch.bool
                        ):
                            direct_result = direct_result.to(torch.bool)
                            interp_result = interp_result.to(torch.bool)
                        else:
                            direct_result = direct_result.to(torch.double)
                            interp_result = interp_result.to(torch.double)

                    self.assertTrue(
                        torch.allclose(
                            direct_result, interp_result, rtol=1e-5, atol=1e-8
                        ),
                        f"Mismatch for {fn}{args}: direct={direct_result}, interp={interp_result}",
                    )

                    if fn in UNARY_BOOL_OPS + BINARY_BOOL_OPS + COMPARE_OPS:
                        self.assertEqual(direct_result.dtype, torch.bool)
                        self.assertEqual(interp_result.dtype, torch.bool)

                    if fn in (
                        "floor_to_int",
                        "ceil_to_int",
                        "round_to_int",
                        "trunc_to_int",
                    ):
                        self.assertEqual(direct_result.dtype, torch.int64)
                        self.assertEqual(interp_result.dtype, torch.int64)

                except NotImplementedError:
                    print(f"Operation {fn} not implemented for TensorReferenceAnalysis")
                except Exception as e:
                    self.fail(f"Unexpected error for {fn}{args}: {str(e)}")