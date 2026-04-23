def _do_pow_for_exponents(self, m1, exponents, pow_fn, atol):
        for num in exponents:
            if (
                isinstance(num, int)
                and num < 0
                and not m1.is_floating_point()
                and not m1.is_complex()
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Integers to negative integer powers are not allowed\.",
                ):
                    torch.pow(m1[4], num)
            else:
                # base - tensor, exponent - number
                # contiguous
                res1 = torch.pow(m1[4], num)
                res2 = res1.clone().zero_()
                # `math.pow` has issues with complex exponentiation so we need to resort to normal `pow`.
                for i in range(res2.size(0)):
                    res2[i] = pow_fn(m1[4][i], num)
                rtol = 0 if atol is not None else None
                self.assertEqual(res1, res2, atol=atol, rtol=rtol)

                # non-contiguous
                res1 = torch.pow(m1[:, 4], num)
                res2 = res1.clone().zero_()
                for i in range(res2.size(0)):
                    res2[i] = pow_fn(m1[i, 4], num)
                self.assertEqual(res1, res2, atol=atol, rtol=rtol)

                # scalar ** tensor to enforce correct handling of dtypes for __rpow__().
                expected_dtype = torch.result_type(num, m1)
                res1 = num ** m1[4]
                res2 = (
                    torch.tensor(num, dtype=expected_dtype, device=m1.device) ** m1[4]
                )
                self.assertEqual(res1, res2)
                self.assertEqual(res1.dtype, expected_dtype)