def test_median_nan_values(self, device, dtype):
        # Generate random 0-3D sizes
        sizes = [random.sample(range(1, 32), i) for i in range(4) for _ in range(2)]
        for size in sizes:
            # Create random input tensor with nan values
            t = torch.rand(size, device=device, dtype=dtype)
            t.masked_fill_(t < 0.1, float('nan'))
            t_numpy = t.cpu().numpy()
            for op in [torch.median, torch.nanmedian]:
                numpy_op = np.median if op == torch.median else np.nanmedian
                res = op(t)
                num_nan = t.isnan().sum()
                if op == torch.median and num_nan > 0:
                    k = t.numel() - 1
                else:
                    k = int((t.numel() - num_nan - 1) / 2)
                self.assertEqual(res, t.view(-1).sort()[0][k])
                if (t.numel() - num_nan) % 2 == 1:
                    # We can only test against numpy for odd reductions because numpy
                    # returns the mean of the two medians and torch returns the lower
                    self.assertEqual(res.item(), numpy_op(t.cpu().numpy()))
                for dim in range(t.ndim):
                    res = op(t, dim, True)
                    size = t.size(dim) if t.ndim > 0 else 1
                    num_nan = t.isnan().sum(dim, True)
                    if op == torch.median:
                        k = torch.where(num_nan > 0, size - 1, int((size - 1) / 2))
                    else:
                        k = ((size - num_nan - 1) / 2).type(torch.long)
                    self.assertEqual(res[0], (t.sort(dim)[0]).gather(dim, k))
                    self.assertEqual(res[0], t.gather(dim, res[1]))
                    # We can only test against numpy for odd reductions because numpy
                    # returns the mean of the two medians and torch returns the lower
                    mask = (size - num_nan) % 2 == 1
                    res = res[0].masked_select(mask).cpu()
                    ref = numpy_op(t_numpy, dim, keepdims=True)[mask.cpu().numpy()]
                    self.assertEqual(res, torch.from_numpy(ref))