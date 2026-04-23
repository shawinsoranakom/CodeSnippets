def test_triton_bsr_scatter_mm(self, device, dtype, blocksize):
        import triton
        from torch.sparse._triton_ops import bsr_scatter_mm, bsr_scatter_mm_indices_data
        from functools import partial
        if isinstance(blocksize, str):
            blocksize = tuple(map(int, blocksize.split('x')))
        else:
            blocksize = (blocksize,) * 2
        # Note that each value in a non-zero block is in range blocksize * [low^2, high^2).
        tensor = partial(make_tensor, device=device, dtype=dtype, low=0.5, high=1.5)

        # NOTE: batch dims with zero sizes are not supported in `to_sparse_bsr`.
        batches = [(), (2,), (2, 2)]
        sizes = [blocksize[0], 2 * blocksize[0], 4 * blocksize[0]]
        sizes_K = [blocksize[1], 2 * blocksize[1]]

        for bd, bs, M, K, N, has_zero_row_block in itertools.product(batches, batches[:1], sizes, sizes_K, sizes, (False, True)):
            bsr_dense = tensor(bs + (M, K))
            if has_zero_row_block:
                if M > blocksize[0]:
                    bsr_dense[:blocksize[0]].zero_()
                else:
                    continue
            bsr = bsr_dense.to_sparse_bsr(blocksize)
            dense = tensor(bd + (K, N))
            expected = bsr.to_dense() @ dense

            for indices_format in ('bsr_strided_mm', 'bsr_strided_mm_compressed', 'scatter_mm'):
                if indices_format in {'bsr_strided_mm', 'bsr_strided_mm_compressed'}:
                    SPLIT_N_list = [N]
                    while SPLIT_N_list[-1] > 1:
                        SPLIT_N_list.append(max(1, SPLIT_N_list[-1] // 2))
                else:
                    SPLIT_N_list = [1]
                for SPLIT_N in SPLIT_N_list:
                    indices_data = bsr_scatter_mm_indices_data(
                        bsr, dense, indices_format=indices_format, SPLIT_N=SPLIT_N)
                    try:
                        result = bsr_scatter_mm(bsr, dense, indices_data=indices_data)
                    except triton.compiler.OutOfResources:
                        # ensure that there was at least one successful test:
                        if SPLIT_N >= SPLIT_N_list[0]:
                            raise AssertionError(f"expected SPLIT_N < {SPLIT_N_list[0]}, got {SPLIT_N}") from None
                        break

                    self.assertEqual(result, expected)
        torch.sparse._triton_ops._bsr_scatter_mm_indices_data.cache_clear()