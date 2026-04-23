def test_randperm(self, device):
        if device == 'cpu' or device == 'meta':
            rng_device = None
        else:
            # TODO: This won't actually work for non-CUDA device
            # see https://github.com/pytorch/pytorch/issues/54282
            rng_device = [device]

        # Test core functionality. On CUDA, different value of n has different
        # code path
        for n in (5, 100, 50000, 100000):
            # Ensure both integer and floating-point numbers are tested. Half follows an execution path that is
            # different from others on CUDA.
            for dtype in (torch.long, torch.half, torch.float, torch.bfloat16):
                if n > 2049 and dtype == torch.half:  # Large n for torch.half will raise an exception, do not test here.
                    continue
                if dtype == torch.bfloat16 and device != 'cpu':
                    continue
                if n > 256 and dtype == torch.bfloat16:
                    continue
                with torch.random.fork_rng(devices=rng_device):
                    res1 = torch.randperm(n, dtype=dtype, device=device)
                res2 = torch.empty(0, dtype=dtype, device=device)
                torch.randperm(n, out=res2, dtype=dtype, device=device)
                self.assertEqual(res1, res2, atol=0, rtol=0)
                self.assertEqual(res1.sort().values.long(), torch.arange(n, device=device))

        # Default type is long
        for n in (100, 10000):
            self.assertEqual(torch.randperm(n, device=device).dtype, torch.long)

        # randperm of 0 elements is an empty tensor
        res1 = torch.randperm(0)
        res2 = torch.tensor(5, dtype=dtype, device=device)
        torch.randperm(0, out=res2)
        self.assertEqual(res1.numel(), 0)
        self.assertEqual(res2.numel(), 0)

        # Test exceptions when n is too large for a floating point type
        for dtype, small_n, large_n in ((torch.uint8, 2**8, 2**8 + 1),
                                        (torch.half, 2**11 + 1, 2**11 + 2),
                                        (torch.float, 2**24 + 1, 2**24 + 2),
                                        (torch.double, 2**25,  # 2**53 + 1 is too large to run
                                         2**53 + 2)):
            res = torch.empty(0, dtype=dtype, device=device)
            torch.randperm(small_n, out=res)  # No exception expected
            self.assertRaises(RuntimeError, lambda: torch.randperm(large_n, out=res, device=device))

        # Test non-contiguous tensors
        for n in (4, 5, 6, 10, 20):
            non_contiguous_tensor = torch.zeros((2, 3), dtype=torch.long, device=device).t()
            self.assertFalse(non_contiguous_tensor.is_contiguous())
            with torch.random.fork_rng(devices=rng_device):
                res = torch.randperm(n, dtype=torch.long, device=device)
            torch.randperm(n, out=non_contiguous_tensor)
            self.assertEqual(non_contiguous_tensor, res)
            self.assertEqual(res.sort().values.long(), torch.arange(n, device=device))