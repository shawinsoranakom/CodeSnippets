def matmul_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp = new_kwargs.pop("input")
    other = new_kwargs.pop("other")

    def _unbind_impl(a, b):
        return [
            func(a_comp, b_comp) for (a_comp, b_comp) in zip(a.unbind(), b.unbind())
        ]

    def _padded_impl(a, b):
        if a.is_nested:
            nt = a
        else:
            nt = b

        from .nested_tensor import nested_from_padded

        min_seqlen = nt._maybe_min_seqlen
        max_seqlen = nt._maybe_max_seqlen
        padded_max_S = max_seqlen
        total_L = nt._values.shape[nt._ragged_idx - 1]
        if padded_max_S is None:
            # use upper bound on max seqlen if it's not present
            padded_max_S = total_L

        padded_shape = (
            *nt.shape[: nt._ragged_idx],
            padded_max_S,
            *nt.shape[nt._ragged_idx + 1 :],
        )
        padded_nt = nt.to_padded_tensor(0.0, output_size=padded_shape)
        if a.is_nested:
            padded_t = func(padded_nt, b)
        else:
            padded_t = func(a, padded_nt)
        return nested_from_padded(
            padded_t,
            offsets=nt._offsets,
            ragged_idx=nt._ragged_idx,
            sum_S=total_L,
            min_seqlen=min_seqlen,
            max_seqlen=max_seqlen,
        )

    # TODO: Back these with proper kernels (e.g. grouped GEMM)
    # NJT x dense
    if inp.is_nested and not other.is_nested:
        # (B, j1, D) x (B, D, E) => (B, j1, E)
        if (
            inp.dim() >= 3
            and inp.dim() == other.dim()
            and inp._ragged_idx < inp.dim() - 1
        ):
            # convert to padded for this
            return _padded_impl(inp, other)
        # Support broadcasting the dense:
        # (B, j1, D) x (D, E) => (B, j1, E)
        # (B, j1, D, E) x (E, F) => (B, j1, D, F)
        # etc.
        elif (
            other.dim() == 2
            and inp.dim() > other.dim()
            and inp._ragged_idx < inp.dim() - 1
        ):
            return NestedTensor(
                func(inp._values, other, **new_kwargs), **extract_kwargs(inp)
            )
    # Dense x NJT
    elif not inp.is_nested and other.is_nested:
        # (B, D, E) x (B, E, j1) => (B, E, j1)
        if other.dim() >= 3 and other.dim() == inp.dim() and other._ragged_idx >= 2:
            # convert to padded for this
            return _padded_impl(inp, other)
        # Support broadcasting the dense:
        # (D, E) x (B, E, j1) => (B, D, j1)
        # (D, E) x (B, E, j1, F) => (B, D, j1, F)
        # etc.
        elif inp.dim() == 2 and other.dim() > inp.dim() and other._ragged_idx >= 2:
            return NestedTensor(
                func(inp, other._values, **new_kwargs), **extract_kwargs(other)
            )

    # NJT x NJT
    elif inp.is_nested and other.is_nested:
        # Support ragged batch dim:
        # (B, j1, D, E) x (B, j1, E, F) => (B, j1, D, F), etc.
        if inp.dim() > 3 and other.dim() > 3 and raggedness_matches(inp, other._size):
            return NestedTensor(func(inp._values, other._values), **extract_kwargs(inp))
        # Support reducing over ragged with dense output:
        # (B, D, j1) x (B, j1, E) => (B, D, E)
        elif (
            inp.dim() == 3
            and other.dim() == 3
            and inp._ragged_idx == 2
            and other._ragged_idx == 1
            and inp.size(inp._ragged_idx) == other.size(other._ragged_idx)
        ):
            # do unbind for this; can't use padded conversion due to j1 in last dim
            return torch.stack(_unbind_impl(inp, other))

    raise RuntimeError(
        f"matmul(): not supported between inputs of shapes {inp._size} and {other.shape}"
    )