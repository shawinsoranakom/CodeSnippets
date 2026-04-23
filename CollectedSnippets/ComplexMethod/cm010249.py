def bsr_dense_addmm(
    input: torch.Tensor,
    bsr: torch.Tensor,
    dense: torch.Tensor,
    *,
    beta=1,
    alpha=1,
    left_alpha: torch.Tensor | None = None,
    right_alpha: torch.Tensor | None = None,
    out: torch.Tensor | None = None,
    skip_checks: bool = False,
    max_grid: tuple[int | None, int | None, int | None] | None = None,
    meta: dict | None = None,
):
    """Compute

      out = beta * input + left_alpha.reshape(-1, 1) * (alpha * (bsr @ dense)) * right_alpha.reshape(1, -1)

    where left_alpha, right_alpha are (* + 1)-D tensors when
    specified, otherwise, these are treated as tensors filled with
    ones.
    """
    f_name = "bsr_dense_addmm"
    values = bsr.values()
    crow_indices = bsr.crow_indices()
    col_indices = bsr.col_indices()
    batch_ndim = crow_indices.dim() - 1
    M, K = bsr.shape[batch_ndim : batch_ndim + 2]
    blocksize = values.shape[batch_ndim + 1 : batch_ndim + 3]
    N = dense.shape[-1]

    # todo: implement checks

    original_batch_dims_broadcasted = broadcast_batch_dims(f_name, bsr, dense)
    if out is None:
        out = dense.new_empty(original_batch_dims_broadcasted + (M, N))

    if bsr._nnz() == 0 or alpha == 0 or N == 0 or M == 0 or K == 0:
        if beta == 0:
            out.zero_()
        else:
            out.copy_(input)
            if beta != 1:
                out.mul_(beta)
        return out

    left_alpha_is_one = False
    right_alpha_is_one = False
    if left_alpha is None:
        left_alpha_is_one = True
        left_alpha = dense.new_empty(()).expand(
            *original_batch_dims_broadcasted, M, N
        )  # not referenced
    else:
        left_alpha = left_alpha.view(*original_batch_dims_broadcasted, M, 1).expand(
            *original_batch_dims_broadcasted, M, N
        )

    if right_alpha is None:
        right_alpha_is_one = True
        right_alpha = dense.new_empty(()).expand(
            *original_batch_dims_broadcasted, M, N
        )  # not referenced
    else:
        right_alpha = right_alpha.view(*original_batch_dims_broadcasted, 1, N).expand(
            *original_batch_dims_broadcasted, M, N
        )
    if left_alpha.stride()[-1] != 0:
        raise AssertionError(
            f"left_alpha.stride()[-1] must be 0, got {left_alpha.stride()[-1]}"
        )
    if right_alpha.stride()[-2] != 0:
        raise AssertionError(
            f"right_alpha.stride()[-2] must be 0, got {right_alpha.stride()[-2]}"
        )

    if meta is None:
        sparsity = round(1 - bsr._nnz() * blocksize[0] * blocksize[1] / (M * K), 2)
        meta = bsr_dense_addmm_meta(
            M,
            K,
            N,
            blocksize[0],
            blocksize[1],
            beta,
            alpha,
            sparsity=sparsity,
            dtype=dense.dtype,
            out_dtype=out.dtype,
        )
    out_backup = out

    (
        crow_indices,
        col_indices,
        values,
        input,
        dense,
        left_alpha,
        right_alpha,
        out,
    ) = prepare_inputs(bsr, input, dense, left_alpha, right_alpha, out)

    BM, BK = blocksize
    SPLIT_N = meta.get("SPLIT_N", N // BM)
    BN = N // SPLIT_N

    out_untiled = out
    out = tile_to_blocksize(out, (BM, BN))
    dense = tile_to_blocksize(dense, (BK, BN))
    input = tile_to_blocksize(input, (BM, BN))
    left_alpha = tile_to_blocksize(left_alpha, (BM, BN))
    right_alpha = tile_to_blocksize(right_alpha, (BM, BN))

    # tl.dot supports float16, float32, int32 as accumulator types.
    dot_out_dtype = {
        torch.float16: tl.float32,
        torch.bfloat16: tl.float32,
        torch.float32: tl.float64,
        torch.float64: tl.float64,
        torch.int8: tl.int32,
        torch.int32: tl.int32,
    }[out.dtype]

    n_batches = dense.size(0)
    n_block_rows = crow_indices.size(-1) - 1
    n_block_cols = dense.size(-3)

    full_grid = (n_batches, n_block_cols, n_block_rows)
    if max_grid is not None:
        grid_blocks = tuple(max_grid[:3][::-1]) + (None,) * (3 - len(max_grid[:3]))
    else:
        grid_blocks = None

    tensor_dims_map = {
        values: (0, None, None),
        crow_indices: (0, None, -1),
        col_indices: (0, None, None),
        input: (0, -3, -4),
        dense: (0, -3, None),
        left_alpha: (0, -3, -4),
        right_alpha: (0, -3, -4),
        out: (0, -3, -4),
    }

    if alpha == 0:
        raise AssertionError("alpha must not be 0")

    def kernel(grid, *sliced_tensors):
        # pyrefly: ignore [unsupported-operation]
        _bsr_strided_addmm_kernel[grid](
            *ptr_stride_extractor(*sliced_tensors),
            beta,
            alpha,
            beta_is_one=beta == 1,
            beta_is_nonzero=beta != 0,
            alpha_is_one=alpha == 1,
            left_alpha_is_one=left_alpha_is_one,
            right_alpha_is_one=right_alpha_is_one,
            BLOCKSIZE_ROW=BM,
            BLOCKSIZE_INNER=BK,
            BLOCKSIZE_COL=BN,
            allow_tf32=dot_out_dtype == tl.float32,
            acc_dtype=dot_out_dtype,
            **meta,
        )

    launch_kernel(kernel, tensor_dims_map, full_grid, grid_blocks)

    if out.data_ptr() != out_backup.data_ptr():
        # prepare_inputs has made a copy of out, copy its content back
        # to out_backup:
        out_backup.copy_(out_untiled.view(out_backup.shape))

    return out_backup