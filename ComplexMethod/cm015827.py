def run_and_check(self, fn, args, dtype=None, *, expect_kernel_count=1):
        # Define fixed tolerances
        RTOL = 1e-5
        ATOL = 1e-6

        # calculate reference value in higher precision when input dtype is float16
        ref_dtype = dtype
        if dtype == torch.float16:
            ref_dtype = torch.float64

        # Cast to the determined reference dtype
        args_ref = [tensor.to(ref_dtype) for tensor in args]

        # Calculate expected output
        raw_expected = fn(*args_ref)

        if isinstance(raw_expected, (tuple, list)):
            # If it's a tuple or list, apply .to(dtype) to each tensor within it
            # Also, handle cases where dtype might not be provided (e.g., for bool reductions)
            if dtype is not None:
                expected = type(raw_expected)(
                    [
                        t.to(dtype) if isinstance(t, torch.Tensor) else t
                        for t in raw_expected
                    ]
                )
            else:
                expected = type(raw_expected)(
                    [
                        t.to(torch.float64) if isinstance(t, torch.Tensor) else t
                        for t in raw_expected
                    ]
                )
        else:
            # If it's a single tensor
            if dtype is not None:
                expected = raw_expected.to(dtype)
            else:
                expected = raw_expected.to(torch.float64)

        fn_compiled = torch.compile(fn, fullgraph=True)
        result, (source_code,) = run_and_get_code(fn_compiled, *args)

        # For comparison, ensure result is also a tuple/list if expected is
        if isinstance(expected, (tuple, list)):
            if isinstance(result, torch.Tensor):
                result = (result,)
            elif not isinstance(result, type(expected)):
                result = type(expected)(result)

            if dtype is not None:
                result = type(result)(
                    [t.to(dtype) if isinstance(t, torch.Tensor) else t for t in result]
                )
            else:
                result = type(result)(
                    [
                        t.to(torch.float64) if isinstance(t, torch.Tensor) else t
                        for t in result
                    ]
                )
        else:
            if dtype is not None and isinstance(result, torch.Tensor):
                result = result.to(dtype)
            elif isinstance(result, torch.Tensor):
                result = result.to(torch.float64)

        # Apply assert_close with fixed tolerances for tensor comparisons
        if isinstance(result, torch.Tensor) and isinstance(expected, torch.Tensor):
            assert_close(result, expected, rtol=RTOL, atol=ATOL)
        elif isinstance(result, (tuple, list)) and isinstance(expected, (tuple, list)):
            # Iterate through elements for comparison
            for r_item, e_item in zip(result, expected):
                if isinstance(r_item, torch.Tensor) and isinstance(
                    e_item, torch.Tensor
                ):
                    assert_close(r_item, e_item, rtol=RTOL, atol=ATOL)
                else:
                    # Fallback to assertEqual for non-tensor elements (e.g., bool, int)
                    self.assertEqual(r_item, e_item)
        else:
            # Fallback to assertEqual for other types not handled by assert_close
            self.assertEqual(result, expected)

        if "@triton_heuristics.fixed_config" in source_code:
            self.assertIn("cooperative_reduction_grid", source_code)
        else:
            self.assertIn("@triton_heuristics.cooperative_reduction", source_code)
        if GPU_TYPE == "cuda":
            self.assertIn("'launch_cooperative_grid': True", source_code)
        if "async_compile.multi_kernel" not in source_code:
            self.assertEqual(
                torch._inductor.metrics.generated_kernel_count, expect_kernel_count
            )
        return source_code