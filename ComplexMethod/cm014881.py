def test_linspace(self, device, dtype):
        _from = random.random()
        to = _from + random.random()
        res1 = torch.linspace(_from, to, 137, device=device, dtype=dtype)
        res2 = torch.tensor((), device=device, dtype=dtype)
        torch.linspace(_from, to, 137, dtype=dtype, out=res2)
        self.assertEqual(res1, res2, atol=0, rtol=0)

        # small tensor
        self.assertEqual(torch.linspace(10, 20, 11, device=device, dtype=dtype),
                         torch.tensor(list(range(10, 21)), device=device, dtype=dtype))
        # large tensor
        if dtype not in (torch.int8, torch.uint8):
            self.assertEqual(torch.linspace(10, 2000, 1991, device=device, dtype=dtype),
                             torch.tensor(list(range(10, 2001)), device=device, dtype=dtype))

        # Vectorization on non-contiguous tensors
        if dtype not in (torch.int8, torch.uint8):  # int8 and uint8 are too small for this test
            res = torch.rand(3, 3, 1000, device=device).to(dtype)
            res = res.permute(2, 0, 1)
            torch.linspace(0, 1000 * 3 * 3, 1000 * 3 * 3, out=res)
            self.assertEqual(res.flatten(), torch.linspace(0, 1000 * 3 * 3, 1000 * 3 * 3, device=device, dtype=dtype))

        self.assertRaises(RuntimeError, lambda: torch.linspace(0, 1, -1, device=device, dtype=dtype))
        # steps = 1
        self.assertEqual(torch.linspace(0, 1, 1, device=device, dtype=dtype),
                         torch.zeros(1, device=device, dtype=dtype), atol=0, rtol=0)
        # steps = 0
        self.assertEqual(torch.linspace(0, 1, 0, device=device, dtype=dtype).numel(), 0, atol=0, rtol=0)

        # steps not provided
        self.assertRaises(TypeError, lambda: torch.linspace(0, 1, device=device, dtype=dtype))

        if dtype == torch.float:
            # passed dtype can't be safely casted to inferred dtype
            with self.assertRaisesRegex(RuntimeError, r"torch.linspace\(\): inferred dtype"):
                torch.linspace(0, 1j, 5, device=device, dtype=dtype)
            with self.assertRaisesRegex(RuntimeError, r"torch.linspace\(\): inferred dtype"):
                torch.linspace(0j, 1, 5, device=device, dtype=dtype)
            with self.assertRaisesRegex(RuntimeError, r"torch.linspace\(\): inferred dtype"):
                torch.linspace(0j, 1j, 5, device=device, dtype=dtype)

        # Check linspace for generating the correct output for each dtype.
        start = 0 if dtype == torch.uint8 else -100
        expected_lin = torch.tensor([start + .5 * i for i in range(401)], device=device, dtype=torch.double)
        actual_lin = torch.linspace(start, start + 200, 401, device=device, dtype=dtype)
        # If on GPU, allow for minor error depending on dtype.
        tol = 0.
        if device != 'cpu':
            if dtype == torch.half:
                tol = 1e-1
            elif dtype == torch.float:
                tol = 1e-5
            elif dtype == torch.double:
                tol = 1e-10

        self.assertEqual(expected_lin.to(dtype), actual_lin, atol=tol, rtol=0)

        # Check linspace for generating with start > end.
        self.assertEqual(torch.linspace(2, 0, 3, device=device, dtype=dtype),
                         torch.tensor((2, 1, 0), device=device, dtype=dtype),
                         atol=0, rtol=0)

        # Check for race condition (correctness when applied on a large tensor).
        if dtype not in (torch.int8, torch.uint8, torch.int16, torch.half, torch.bfloat16):
            y = torch.linspace(0, 999999 + (999999j if dtype.is_complex else 0),
                               1000000, device=device, dtype=dtype)
            if dtype.is_complex:
                cond = torch.logical_and(y[:-1].real < y[1:].real, y[:-1].imag < y[1:].imag)
            else:
                cond = y[:-1] < y[1:]
            correct = all(cond)
            self.assertTrue(correct)

        # Check linspace for non-contiguous tensors.
        x = torch.zeros(2, 3, device=device, dtype=dtype)
        y = torch.linspace(0, 3, 4, out=x.narrow(1, 1, 2), dtype=dtype)
        self.assertEqual(x, torch.tensor(((0, 0, 1), (0, 2, 3)), device=device, dtype=dtype), atol=0, rtol=0)