def test_index_reduce(self, device, dtype, reduce):
        size = (3, 4, 5)
        index_dtypes = [torch.int, torch.long]
        include_selfs = [True, False]
        noncontig_opts = [True, False]
        amin_init = float("inf") if dtype.is_floating_point else torch.iinfo(dtype).max
        amax_init = -float("inf") if dtype.is_floating_point else torch.iinfo(dtype).min
        reduction_init = {"prod": 1, "mean": 0, "amin": amin_init, "amax": amax_init}

        for dest_noncontig, src_noncontig, index_noncontig in product(
            noncontig_opts, repeat=3
        ):
            for idx_dtype, include_self in product(index_dtypes, include_selfs):
                for dim in range(len(size)):
                    num_src = np.random.randint(10)
                    num_dest = size[dim]
                    dest = make_tensor(
                        size, device=device, dtype=dtype, noncontiguous=dest_noncontig
                    )
                    src_size = size[:dim] + (num_src,) + size[dim + 1 :]
                    src = make_tensor(
                        src_size,
                        device=device,
                        dtype=dtype,
                        noncontiguous=src_noncontig,
                    )
                    idx = torch.testing.make_tensor(
                        num_src,
                        low=0,
                        high=num_dest,
                        dtype=idx_dtype,
                        device=device,
                        noncontiguous=index_noncontig,
                    )
                    expected = dest.clone()
                    dest.index_reduce_(dim, idx, src, reduce, include_self=include_self)
                    # fill rows in idx with reduction inits if include_self=False
                    if not include_self:
                        expected.index_fill_(dim, idx.long(), reduction_init[reduce])
                    expected = expected.transpose(0, dim)
                    src = src.transpose(0, dim)
                    for i in range(num_src):
                        if reduce == "prod":
                            expected[idx[i]] *= src[i]
                        elif reduce == "amin":
                            torch.minimum(
                                expected[idx[i]], src[i], out=expected[idx[i]]
                            )
                        elif reduce == "amax":
                            torch.maximum(
                                expected[idx[i]], src[i], out=expected[idx[i]]
                            )
                        else:
                            expected[idx[i]] += src[i]
                    if reduce == "mean":
                        counts = (
                            torch.ones_like(expected)
                            if include_self
                            else torch.zeros_like(expected)
                        )
                        counts.index_add_(0, idx, torch.ones_like(src))
                        counts.masked_fill_(counts == 0, 1)
                        if dtype.is_floating_point:
                            expected.div_(counts)
                        else:
                            expected.div_(counts, rounding_mode="floor")
                    expected = expected.transpose(0, dim)

                    # MPS uses atomics for index_reduce which causes
                    # non-deterministic rounding for low-precision types
                    kwargs = {}
                    if (
                        "mps" in device
                        and dtype in [torch.bfloat16, torch.float16]
                        and reduce in ["mean", "prod"]
                    ):
                        kwargs = {"atol": 0.02, "rtol": 0.1}
                    self.assertEqual(dest, expected, **kwargs)