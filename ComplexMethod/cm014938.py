def _test_minmax_helper(self, torchfn, reffn, device, dtype, skip_indices=False):
        def create_input(shape, device, dtype):
            if dtype.is_floating_point:
                return torch.randn(*shape, device=device, dtype=dtype)
            else:
                low = 0 if dtype == torch.bool else -1000
                high = 2 if dtype == torch.bool else 1000
                return torch.randint(low, high, shape, device=device, dtype=dtype)
        x = create_input((100, 100), device, dtype)
        self.compare_with_numpy(torchfn, reffn, x)
        # non contiguous
        x = create_input((10, 10, 10), device, dtype)
        x = x[:, 4]
        self.compare_with_numpy(torchfn, reffn, x)

        def get_values(x):
            if isinstance(x, tuple):
                return x[0]
            return x

        # indices
        if not skip_indices:
            size = 5
            x = create_input((size, size), device, dtype)
            inputs = (x, x.t())
            dims = (0, 1)
            for xinp, d in product(inputs, dims):
                self.compare_with_numpy(lambda x: get_values(torchfn(x, d, False)), lambda x: reffn(x, d, keepdims=False), xinp)
                result = torchfn(xinp, d, False)
                if isinstance(result, tuple):
                    v, i = result
                    if d == 1:
                        self.assertEqual(xinp[torch.arange(size), i], v, atol=0, rtol=0)
                    else:
                        self.assertEqual(xinp[i, torch.arange(size)], v, atol=0, rtol=0)
        # nan
        if dtype.is_floating_point:
            for index in (0, 4, 99):
                x = create_input((100,), device, dtype)
                x[index] = nan
                if not skip_indices:
                    result = torchfn(x, 0)
                    v = get_values(result)
                    self.assertEqual(v, nan)
                    if isinstance(result, tuple):
                        i = result[1]
                        self.assertEqual(i, index)
                self.assertEqual(torchfn(x), nan)