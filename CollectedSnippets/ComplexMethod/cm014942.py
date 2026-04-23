def test_median_real_values(self, device, dtype):
        # Generate random 0-3D sizes
        sizes = [random.sample(range(1, 32), i) for i in range(4) for _ in range(2)]
        for size in sizes:
            # Create random input tensor
            t = torch.randn(size, device=device).type(dtype)
            t_numpy = t.cpu().numpy()
            res = t.median()
            self.assertEqual(res, t.nanmedian())
            k = int((t.numel() - 1) / 2)
            self.assertEqual(res, t.view(-1).sort()[0][k])
            if t.numel() % 2 == 1:
                # We can only test against numpy for odd reductions because numpy
                # returns the mean of the two medians and torch returns the lower
                self.assertEqual(res.cpu().numpy(), np.median(t_numpy))
            for dim in range(t.ndim):
                res = t.median(dim, True)
                self.assertEqual(res, t.nanmedian(dim, True))
                size = t.size(dim) if t.ndim > 0 else 1
                k = int((size - 1) / 2)
                self.assertEqual(res[0], (t.sort(dim)[0]).select(dim, k).unsqueeze_(dim))
                self.assertEqual(res[0], t.gather(dim, res[1]))
                if size % 2 == 1:
                    # We can only test against numpy for odd reductions because numpy
                    # returns the mean of the two medians and torch returns the lower
                    self.assertEqual(res[0].cpu().numpy(), np.median(t_numpy, dim, keepdims=True), exact_dtype=False)