def tune_bsr_dense_addmm(
    input,
    bsr,
    dense,
    *,
    beta=1,
    alpha=1,
    left_alpha=None,
    right_alpha=None,
    out=None,
    store=False,
    verbose=False,
    force=False,
    opname=None,
):
    """Tune bsr_dense_addmm kernel parameters against the given inputs.

    When store is True, the tuning results will be stored in the
    database of kernel parameters.
    """
    import triton

    if opname is None:
        opname = "bsr_dense_addmm"

    if opname == "_int_bsr_dense_addmm":
        from torch.sparse._triton_ops import _int_bsr_dense_addmm as bsr_dense_addmm
    else:
        from torch.sparse._triton_ops import bsr_dense_addmm

    N = dense.shape[-1]
    values = bsr.values()
    crow_indices = bsr.crow_indices()
    batch_ndim = crow_indices.dim() - 1
    M, K = bsr.shape[batch_ndim : batch_ndim + 2]
    BM, BK = values.shape[batch_ndim + 1 : batch_ndim + 3]

    # Reference parameters is a set of parameters that leads to a
    # successful kernel call and the corresponding timing is used as a
    # reference for computing speedups. Avoid changing the reference
    # parameters when possible.
    reference_meta = dict(
        GROUP_SIZE_ROW=1, num_stages=1, num_warps=4, SPLIT_N=max(N // BM, 1)
    )

    # Compute the key of parameters:
    sparsity = round(1 - bsr._nnz() * BM * BK / (M * K), 2)
    dtype = bsr.dtype
    if out is None:
        out_dtype = dtype
    else:
        out_dtype = out.dtype
    if out_dtype is dtype:
        version_dtype = dtype
    else:
        version_dtype = (dtype, out_dtype)
    version = (0, version_dtype, sparsity)
    key = (M, K, N, BM, BK, beta == 0, beta == 1, alpha == 1)

    # For tuning, for an initial state, use parameters from the
    # database if available, otherwise, use the reference parameters.
    initial_meta = get_meta(opname, key, version=version, exact=True)
    if initial_meta is None:
        may_skip_update = False
        initial_meta = get_meta(opname, key, version=(0, dtype, 0.5), exact=True)
        if initial_meta is None:
            initial_meta = reference_meta
    elif not force:
        return initial_meta
    else:
        may_skip_update = True

    # The target function that is minimized in the tuning process:
    def bench(meta, input=input, bsr=bsr, dense=dense, alpha=alpha, out=out):
        def test_func():
            return bsr_dense_addmm(
                input,
                bsr,
                dense,
                beta=beta,
                alpha=alpha,
                left_alpha=left_alpha,
                right_alpha=right_alpha,
                meta=meta,
                out=out,
            )

        return triton.testing.do_bench(test_func, warmup=500, rep=100)

    # The step function that increments a specified meta parameter:
    def step_meta_parameter(name, value, direction, meta, M=M, N=N, K=K, BM=BM, BK=BK):
        # return next value in positive or negative direction, or
        # input value if the step will result an invalid
        # value. The input value is assumed to be valid.
        is_log = name in {"SPLIT_N", "num_warps"}
        min_value = dict(SPLIT_N=1, num_warps=1, num_stages=1, GROUP_SIZE_ROW=1)[name]
        max_value = dict(SPLIT_N=max(N // BM, 1)).get(name)
        value_step = dict(SPLIT_N=2, num_warps=2, num_stages=1, GROUP_SIZE_ROW=1)[name]
        if is_log:
            next_value = (
                value * value_step**direction
                if direction > 0
                else value // (value_step ** abs(direction))
            )
        else:
            next_value = value + value_step * direction
        if min_value is not None:
            next_value = max(next_value, min_value)
        if max_value is not None:
            next_value = min(next_value, max_value)
        if name == "SPLIT_N" and N % next_value != 0:
            return value
        return next_value

    # Tune:
    meta, speedup, timing, sensitivity_message = minimize(
        bench,
        initial_meta,
        reference_meta,
        step_meta_parameter,
        max_step=2,
        verbose=verbose,
    )
    if verbose:
        print(f"-> {sensitivity_message}, {speedup=:.1f} %, {timing=:.3f} ms")

    if store and not (
        may_skip_update and meta == initial_meta and initial_meta is not reference_meta
    ):
        device_name = _get_device_name()
        update(
            opname,
            device_name,
            version,
            key,
            tuple(meta[k] for k in sorted(meta)),
        )

    return meta