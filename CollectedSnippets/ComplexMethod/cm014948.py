def _test_scatter_base(self, fn, *, device, dtype, is_scalar, reduction,
                           unique_indices=True, include_self=True):
        m, n, o = random.randint(10, 20), random.randint(10, 20), random.randint(10, 20)
        elems_per_row = random.randint(1, 10)
        dim = random.randrange(3)

        idx_size = [m, n, o]
        idx_size[dim] = elems_per_row
        idx = torch.empty(tuple(idx_size), device=device, dtype=torch.long)
        self._fill_indices(idx, dim, ([m, n, o])[dim], elems_per_row, m, n, o, unique_indices)

        if is_scalar:
            src = random.random()
        else:
            src_size = [random.randint(1, 5) + s for s in idx_size]
            src = make_tensor(tuple(src_size), device=device, dtype=dtype)

        base = make_tensor((m, n, o), device=device, dtype=dtype)
        if reduction is not None:
            if fn is torch.Tensor.scatter_reduce_:
                actual = fn(base.clone(), dim, idx, src, reduce=reduction, include_self=include_self)
            else:
                actual = fn(base.clone(), dim, idx, src, reduce=reduction)
        else:
            actual = fn(base.clone(), dim, idx, src)

        expected = base.clone()
        counts = torch.zeros(base.shape, dtype=torch.long, device=device) + include_self
        for i in range(idx_size[0]):
            for j in range(idx_size[1]):
                for k in range(idx_size[2]):
                    ii = [i, j, k]
                    ii[dim] = idx[i, j, k]
                    if fn is torch.Tensor.scatter_add_:
                        expected[tuple(ii)] += src[i, j, k]
                    else:
                        # method may be 'scatter_', 'scatter', 'scatter_reduce'
                        # or 'scatter_reduce_', the former two might have a reduction argument
                        # while the latter two always do
                        value = src if is_scalar else src[i, j, k]

                        if ((not include_self) and counts[tuple(ii)] == 0):
                            expected[tuple(ii)] = value
                        else:
                            if reduction == "add" or reduction == "sum":
                                expected[tuple(ii)] += value
                            elif reduction == "multiply" or reduction == "prod":
                                expected[tuple(ii)] *= value
                            elif reduction == "amax":
                                expected[tuple(ii)] = max(expected[tuple(ii)], value)
                            elif reduction == "amin":
                                expected[tuple(ii)] = min(expected[tuple(ii)], value)
                            elif reduction == "mean":
                                expected[tuple(ii)] += value
                            else:
                                expected[tuple(ii)] = value

                        counts[tuple(ii)] += 1

        if (reduction == "mean"):
            counts.masked_fill_(counts == 0, 1)
            if (dtype.is_floating_point or dtype.is_complex):
                expected /= counts
            else:
                expected.div_(counts, rounding_mode="floor")

        if dtype == torch.float16 or dtype == torch.bfloat16:
            # Some CUDA kernels (e.g. indexing_backward_kernel_stride_1) that are called during
            # the test use fp32 for internal accumulation for improved accuracy. When using 16 bit
            # precision types can be small differences
            self.assertEqual(actual, expected, atol=0.04, rtol=0.05)
        else:
            # When we are running opportunistic_fastatomics, we will expect some floating point rounding
            # errors as the order of operation is not guaranteed.
            if TEST_WITH_ROCM and CDNA3OrLater() \
                    and not torch.are_deterministic_algorithms_enabled():
                self.assertEqual(actual, expected, atol=1e-9, rtol=1e-6)
            else:
                self.assertEqual(actual, expected, atol=0, rtol=0)

        # Tests empty index
        dst = make_tensor((2, 2), device=device, dtype=dtype)
        idx = torch.tensor((), device=device, dtype=torch.long)
        src = make_tensor((2, 2), device=device, dtype=dtype)
        if reduction is not None:
            actual = fn(dst, 0, idx, src, reduce=reduction)
        else:
            actual = fn(dst, 0, idx, src)
        self.assertEqual(actual, dst, atol=0, rtol=0)