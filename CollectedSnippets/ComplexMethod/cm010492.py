def _unique(
    fake_mode: FakeTensorMode,
    func: OpOverload,
    arg: FakeTensor,
    dim: int | None,
    sorted: bool = True,
    return_inverse: bool = False,
    return_counts: bool = False,
    *,
    unique_consecutive: bool = False,
) -> tuple[FakeTensor, FakeTensor, FakeTensor]:
    if (
        fake_mode.shape_env is None
        or not fake_mode.shape_env.allow_dynamic_output_shape_ops
    ):
        # Without symints/symfloats, cannot handle this
        raise DynamicOutputShapeException(func)

    nnz = arg.unique_consecutive_memo if unique_consecutive else arg.unique_memo

    # Do not use a memo for unique_dim
    if dim is not None or nnz is None:
        # Avoid importing sympy at a module level
        from torch.fx.experimental.symbolic_shapes import (
            _constrain_range_for_size,
            has_free_symbols,
        )

        if not has_free_symbols(arg.numel()) and arg.numel() == 0:
            # If numel is zero, then the output size must be zero.
            # In this case, we must not allocate an unbacked SymInt,
            # because if we do, it will immediately get refined to
            # zero, but this will be inconsistent with size oblivious
            # tests (which will continue to claim that the unbacked
            # symint cannot equal zero).  We could also unconditionally
            # allocate an unbacked SymInt and not refine its range,
            # but this seems more precise.
            nnz = 0
        else:
            nnz = fake_mode.shape_env.create_unbacked_symint()

            maxval = sys.maxsize - 1

            numel = arg.numel() if dim is None else arg.size(dim)
            if not has_free_symbols(numel):
                maxval = int(numel)

            _constrain_range_for_size(nnz, max=maxval)

        if dim is None:
            if unique_consecutive:
                arg.unique_consecutive_memo = nnz  # pyrefly: ignore[bad-assignment]
            else:
                arg.unique_memo = nnz  # pyrefly: ignore[bad-assignment]

    if dim is None:
        # pyrefly: ignore[no-matching-overload]
        ret = [arg.new_empty((nnz,))]
    else:
        # pyrefly: ignore[no-matching-overload]
        ret = [arg.new_empty(*arg.shape[:dim], nnz, *arg.shape[dim + 1 :])]

    return_if_dim_and_cpu = dim is not None and arg.fake_device == torch.device("cpu")
    if return_inverse or return_if_dim_and_cpu:
        inverse = arg.new_empty(
            arg.shape if dim is None else (arg.shape[dim],), dtype=torch.int64
        )
    else:
        inverse = arg.new_empty(0, dtype=torch.int64)
    ret.append(inverse)

    if return_counts or return_if_dim_and_cpu:
        counts = arg.new_empty(
            ret[0].shape if dim is None else (ret[0].shape[dim],), dtype=torch.int64
        )
    else:
        counts = arg.new_empty(0, dtype=torch.int64)
    ret.append(counts)

    return tuple(ret)