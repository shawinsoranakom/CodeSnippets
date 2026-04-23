def test_cond_errors_and_warnings(self, device, dtype):
        norm_types = [1, -1, 2, -2, inf, -inf, 'fro', 'nuc', None]

        # cond expects the input to be at least 2-dimensional
        a = torch.ones(3, dtype=dtype, device=device)
        for p in norm_types:
            with self.assertRaisesRegex(RuntimeError, r'at least 2 dimensions'):
                torch.linalg.cond(a, p)

        # for some norm types cond expects the input to be square
        a = torch.ones(3, 2, dtype=dtype, device=device)
        norm_types = [1, -1, inf, -inf, 'fro', 'nuc']
        for p in norm_types:
            with self.assertRaisesRegex(RuntimeError, r'must be batches of square matrices'):
                torch.linalg.cond(a, p)

        # if non-empty out tensor with wrong shape is passed a warning is given
        a = torch.ones((2, 2), dtype=dtype, device=device)
        for p in ['fro', 2]:
            real_dtype = a.real.dtype if dtype.is_complex else dtype
            out = torch.empty(a.shape, dtype=real_dtype, device=device)
            with warnings.catch_warnings(record=True) as w:
                # Trigger warning
                torch.linalg.cond(a, p, out=out)
                # Check warning occurs
                self.assertEqual(len(w), 1)
                self.assertTrue("An output with one or more elements was resized" in str(w[-1].message))

        # dtypes should be safely castable
        out = torch.empty(0, dtype=torch.int, device=device)
        for p in ['fro', 2]:
            with self.assertRaisesRegex(RuntimeError, "but got result with dtype Int"):
                torch.linalg.cond(a, p, out=out)

        # device should match
        if torch.cuda.is_available():
            wrong_device = 'cpu' if self.device_type != 'cpu' else 'cuda'
            out = torch.empty(0, dtype=dtype, device=wrong_device)
            for p in ['fro', 2]:
                with self.assertRaisesRegex(RuntimeError, "tensors to be on the same device"):
                    torch.linalg.cond(a, p, out=out)

        # for batched input if at least one matrix in the batch is not invertible,
        # we can't get the result for all other (possibly) invertible matrices in the batch without an explicit for loop.
        # this should change when at::inverse works with silent errors
        # NumPy works fine in this case because it's possible to silence the error and get the inverse matrix results
        # possibly filled with NANs
        batch_dim = 3
        a = torch.eye(3, 3, dtype=dtype, device=device)
        a = a.reshape((1, 3, 3))
        a = a.repeat(batch_dim, 1, 1)
        a[1, -1, -1] = 0  # now a[1] is singular
        for p in [1, -1, inf, -inf, 'fro', 'nuc']:
            result = torch.linalg.cond(a, p)
            self.assertEqual(result[1], float('inf'))

        # check invalid norm type
        a = torch.ones(3, 3, dtype=dtype, device=device)
        for p in ['wrong_norm', 5]:
            with self.assertRaisesRegex(RuntimeError, f"linalg.cond got an invalid norm type: {p}"):
                torch.linalg.cond(a, p)