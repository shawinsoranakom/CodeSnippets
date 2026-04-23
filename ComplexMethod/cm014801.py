def test_float_power(self, device, dtypes):
        def to_np(value):
            if isinstance(value, torch.Tensor) and value.dtype == torch.bfloat16:
                return value.to(torch.float).cpu().numpy()
            return value.cpu().numpy() if isinstance(value, torch.Tensor) else value

        base_dtype = dtypes[0]
        exp_dtype = dtypes[1]
        out_dtype = (
            torch.complex128
            if base_dtype.is_complex or exp_dtype.is_complex
            else torch.float64
        )

        base = make_tensor((30,), dtype=base_dtype, device=device, low=1, high=100)
        # Complex and real results do not agree between PyTorch and NumPy when computing negative and zero power of 0
        # Related: https://github.com/pytorch/pytorch/issues/48000
        # base[0] = base[3] = base[7] = 0
        exp = make_tensor((30,), dtype=exp_dtype, device=device, low=-2, high=2)
        exp[0] = exp[4] = exp[6] = 0

        expected = torch.from_numpy(np.float_power(to_np(base), to_np(exp)))

        exponents = [-2.8, -2, -1, -0.5, 0.5, 1, 2]
        complex_exponents = exponents + [
            -2.5j,
            -1.0j,
            1.0j,
            2.5j,
            1.0 + 1.0j,
            -1.0 - 1.5j,
            3.3j,
        ]

        for op in (
            torch.float_power,
            torch.Tensor.float_power,
            torch.Tensor.float_power_,
        ):
            # Case of Tensor x Tensor
            if op is torch.Tensor.float_power_ and base_dtype != out_dtype:
                with self.assertRaisesRegex(
                    RuntimeError, "operation's result requires dtype"
                ):
                    op(base.clone(), exp)
            else:
                result = op(base.clone(), exp)
                self.assertEqual(expected, result)

            if op is torch.float_power:
                out = torch.empty_like(base).to(device=device, dtype=out_dtype)
                op(base, exp, out=out)
                self.assertEqual(expected, out)

            # Case of Tensor x Scalar
            for i in complex_exponents if exp_dtype.is_complex else exponents:
                out_dtype_scalar_exp = (
                    torch.complex128
                    if base_dtype.is_complex or type(i) is complex
                    else torch.float64
                )
                expected_scalar_exp = torch.from_numpy(np.float_power(to_np(base), i))

                if (
                    op is torch.Tensor.float_power_
                    and base_dtype != out_dtype_scalar_exp
                ):
                    with self.assertRaisesRegex(
                        RuntimeError, "operation's result requires dtype"
                    ):
                        op(base.clone(), i)
                else:
                    result = op(base.clone(), i)
                    self.assertEqual(expected_scalar_exp, result)

                if op is torch.float_power:
                    out = torch.empty_like(base).to(
                        device=device, dtype=out_dtype_scalar_exp
                    )
                    op(base, i, out=out)
                    self.assertEqual(expected_scalar_exp, out)

        # Case of Scalar x Tensor
        for i in complex_exponents if base_dtype.is_complex else exponents:
            out_dtype_scalar_base = (
                torch.complex128
                if exp_dtype.is_complex or type(i) is complex
                else torch.float64
            )
            expected_scalar_base = torch.from_numpy(np.float_power(i, to_np(exp)))

            result = torch.float_power(i, exp)
            self.assertEqual(expected_scalar_base, result)

            out = torch.empty_like(exp).to(device=device, dtype=out_dtype_scalar_base)
            torch.float_power(i, exp, out=out)
            self.assertEqual(expected_scalar_base, out)