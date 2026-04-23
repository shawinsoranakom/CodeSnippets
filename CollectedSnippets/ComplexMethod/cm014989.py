def test_cond(self, device, dtype):
        def run_test_case(input, p):
            result = torch.linalg.cond(input, p)
            result_numpy = np.linalg.cond(input.cpu().numpy(), p)
            self.assertEqual(result, result_numpy, rtol=1e-2, atol=self.precision, exact_dtype=False)
            self.assertEqual(result.shape, result_numpy.shape)

            # test out= variant
            out = torch.empty_like(result)
            ans = torch.linalg.cond(input, p, out=out)
            self.assertEqual(ans, out)
            self.assertEqual(ans, result)

        norm_types = [1, -1, 2, -2, inf, -inf, 'fro', 'nuc', None]
        input_sizes = [(32, 32), (2, 3, 3, 3)]
        for input_size in input_sizes:
            input = torch.randn(*input_size, dtype=dtype, device=device)
            for p in norm_types:
                run_test_case(input, p)

        # test empty batch sizes
        input_sizes = [(0, 3, 3), (0, 2, 5, 5)]
        for input_size in input_sizes:
            input = torch.randn(*input_size, dtype=dtype, device=device)
            for p in norm_types:
                run_test_case(input, p)

        # test non-square input
        input_sizes = [(16, 32), (32, 16), (2, 3, 5, 3), (2, 3, 3, 5)]
        for input_size in input_sizes:
            input = torch.randn(*input_size, dtype=dtype, device=device)
            for p in [2, -2, None]:
                run_test_case(input, p)

        # test for singular input
        a = torch.eye(3, dtype=dtype, device=device)
        a[-1, -1] = 0  # make 'a' singular
        for p in norm_types:
            try:
                run_test_case(a, p)
            except np.linalg.LinAlgError:
                # Numpy may fail to converge for some BLAS backends (although this is very rare)
                # See the discussion in https://github.com/pytorch/pytorch/issues/67675
                pass

        # test for 0x0 matrices. NumPy doesn't work for such input, we return 0
        input_sizes = [(0, 0), (2, 5, 0, 0)]
        for input_size in input_sizes:
            input = torch.randn(*input_size, dtype=dtype, device=device)
            for p in ['fro', 2]:
                expected_dtype = a.real.dtype if dtype.is_complex else dtype
                expected = torch.zeros(input_size[:-2], dtype=expected_dtype, device=device)
                actual = torch.linalg.cond(input, p)
                self.assertEqual(actual, expected)