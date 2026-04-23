def test_pow(self, device, dtype):
        m1 = torch.empty(0, dtype=dtype, device=device)
        if m1.is_floating_point() or m1.is_complex():
            m1 = (
                make_tensor((100, 100), low=0, high=1, dtype=dtype, device=device) + 0.5
            )
        else:
            # math.pow will overflow and throw exceptions for large integers
            range_high = 4 if dtype in (torch.int8, torch.uint8) else 10
            m1 = make_tensor(
                (100, 100), low=1, high=range_high, dtype=dtype, device=device
            )

        exponents = [-2.8, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 4, 3.3, True, False]
        complex_exponents = [
            -2.5j,
            -1.0j,
            0j,
            1.0j,
            2.5j,
            1.0 + 1.0j,
            -1.0 - 1.5j,
            3.3j,
        ]
        if m1.is_complex():
            self._do_pow_for_exponents(m1, exponents + complex_exponents, pow, 10e-4)
        else:
            self._do_pow_for_exponents(m1, exponents, math.pow, None)
            will_raise_error = (
                dtype is torch.half and torch.device(device).type == "cpu"
            )
            if will_raise_error:
                # On CPU,
                # Half Tensor with complex exponents leads to computation dtype
                # of ComplexHalf for which this ops is not supported yet
                with self.assertRaisesRegex(
                    RuntimeError, "not implemented for 'ComplexHalf'"
                ):
                    self._do_pow_for_exponents(m1, complex_exponents, pow, 10e-4)
            else:
                self._do_pow_for_exponents(m1, complex_exponents, pow, 10e-4)

        # base - number, exponent - tensor
        # contiguous
        res1 = torch.pow(3, m1[4])
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = pow(3, m1[4, i])
        self.assertEqual(res1, res2)

        # non-contiguous
        res1 = torch.pow(3, m1[:, 4])
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = pow(3, m1[i][4])
        self.assertEqual(res1, res2)