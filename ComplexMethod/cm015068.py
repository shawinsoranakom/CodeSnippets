def generate_samples():
            from itertools import chain, combinations

            for sizes in [(1025,), (10000,)]:
                size = sizes[0]
                # binary strings
                yield (torch.tensor([0, 1] * size, dtype=dtype, device=device), 0)

            if self.device_type == "cuda":
                return

            yield (torch.tensor([0, 1] * 100, dtype=dtype, device=device), 0)

            def repeated_index_fill(t, dim, idxs, vals):
                res = t
                for idx, val in zip(idxs, vals):
                    res = res.index_fill(dim, idx, val)
                return res

            for sizes in [(1, 10), (10, 1), (10, 10), (10, 10, 10)]:
                size = min(*sizes)
                x = (torch.randn(*sizes, device=device) * size).to(dtype)
                yield (x, 0)

                # Generate tensors which are being filled at random locations
                # with values from the non-empty subsets of the set (inf, neg_inf, nan)
                # for each dimension.
                n_fill_vals = 3  # cardinality of (inf, neg_inf, nan)
                for dim in range(len(sizes)):
                    idxs = (
                        torch.randint(high=size, size=(size // 10,))
                        for i in range(n_fill_vals)
                    )
                    vals = (inf, neg_inf, nan)
                    subsets = chain.from_iterable(
                        combinations(list(zip(idxs, vals)), r)
                        for r in range(1, n_fill_vals + 1)
                    )
                    for subset in subsets:
                        idxs_subset, vals_subset = zip(*subset)
                        yield (
                            repeated_index_fill(x, dim, idxs_subset, vals_subset),
                            dim,
                        )