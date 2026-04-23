def helper(dtype):
            def ensure_tuple(x):
                if isinstance(x, torch.Tensor):
                    return (x,)
                return x

            if dtype is torch.bool:
                x = torch.tensor([True, False, False, False, True, False, True, False], dtype=torch.bool, device=device)
                expected_unique = torch.tensor([False, True], dtype=torch.bool, device=device)
                expected_inverse = torch.tensor([1, 0, 0, 0, 1, 0, 1, 0], dtype=torch.long, device=device)
                expected_counts = torch.tensor([5, 3], dtype=torch.long, device=device)
            else:
                x = torch.tensor([1, 2, 3, 2, 8, 5, 2, 3], dtype=dtype, device=device)
                expected_unique = torch.tensor([1, 2, 3, 5, 8], dtype=dtype, device=device)
                expected_inverse = torch.tensor([0, 1, 2, 1, 4, 3, 1, 2], device=device)
                expected_counts = torch.tensor([1, 3, 2, 1, 1], device=device)

            # test sorted unique
            fs = (
                lambda x, **kwargs: torch.unique(x, sorted=True, **kwargs),
                lambda x, **kwargs: x.unique(sorted=True, **kwargs),
            )
            x_sliced = torch.empty(x.size(0) * 2, dtype=dtype, device=device)[::2].copy_(x)
            xs = (x, x_sliced)
            for f, x in product(fs, xs):
                self._test_unique_with_expects(device, dtype, f, x, expected_unique, expected_inverse, expected_counts, (2, 2, 2))
                self._test_unique_scalar_empty(dtype, device, f)

            # test unsorted unique
            fs = (
                lambda x, **kwargs: torch.unique(x, sorted=False, **kwargs),
                lambda x, **kwargs: x.unique(sorted=False, **kwargs)
            )
            for f, x in product(fs, xs):
                self._test_unique_scalar_empty(dtype, device, f)
                for return_inverse, return_counts in product((True, False), repeat=2):
                    ret = ensure_tuple(f(x, return_inverse=return_inverse, return_counts=return_counts))
                    self.assertEqual(len(ret), 1 + int(return_inverse) + int(return_counts))
                    x_list = x.tolist()
                    x_unique_list = ret[0].tolist()
                    self.assertEqual(expected_unique.tolist(), sorted(x_unique_list))
                    if return_inverse:
                        x_inverse_list = ret[1].tolist()
                        for i, j in enumerate(x_inverse_list):
                            self.assertEqual(x_list[i], x_unique_list[j])
                    if return_counts:
                        count_index = 1 + int(return_inverse)
                        x_counts_list = ret[count_index].tolist()
                        for i, j in zip(x_unique_list, x_counts_list):
                            count = 0
                            for k in x_list:
                                if k == i:
                                    count += 1
                            self.assertEqual(j, count)