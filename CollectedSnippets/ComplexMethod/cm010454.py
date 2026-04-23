def index_put_(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp: NestedTensor = new_kwargs.pop("input")

    # For index_put_ to work, we add together the indices of the ragged dimension
    # and the batch dimension, adding the offsets of each ragged dimension to its
    # indices

    indices = new_kwargs.pop("indices")

    if len(indices) > inp.dim():
        raise AssertionError(
            f"Too many indices: got {len(indices)} but tensor has {inp.dim()} dimensions"
        )

    if len(indices) < inp._ragged_idx + 1:
        if not inp.is_contiguous():
            raise RuntimeError(
                "index_put(): If ragged dimension is not part of indices, this only works on contiguous NJTs"
            )
        # Ragged dim is NOT part of indices, we need to pad the nested tensor to apply func
        from .nested_tensor import nested_from_padded

        min_seqlen = inp._maybe_min_seqlen
        max_seqlen = inp._maybe_max_seqlen
        padded_max_S = max_seqlen
        total_L = inp._values.shape[inp._ragged_idx - 1]
        if padded_max_S is None:
            # use upper bound on max seqlen if it's not present
            padded_max_S = total_L

        padded_shape = (
            *inp.shape[: inp._ragged_idx],
            padded_max_S,
            *inp.shape[inp._ragged_idx + 1 :],
        )
        padded_inp = inp.to_padded_tensor(0.0, output_size=padded_shape)
        new_njt = nested_from_padded(
            func(padded_inp, indices, **new_kwargs),
            offsets=inp._offsets,
            ragged_idx=inp._ragged_idx,
            sum_S=total_L,
            min_seqlen=min_seqlen,
            max_seqlen=max_seqlen,
        )

        if func is torch.ops.aten.index_put_.default:
            inp._values.copy_(new_njt.values())
            return inp
        return new_njt

    # We can run on the underlying values directly

    # Validate indices
    if inp.lengths() is None:
        lengths = inp.offsets().diff()
    else:
        lengths = inp.lengths()
    torch._assert_async(
        # pyrefly: ignore [no-matching-overload]
        torch.all(indices[inp._ragged_idx] < lengths),
        "Some indices in the ragged dimension are out of bounds!",
    )

    # Recompute indices for _values
    ragged_indices = inp.offsets()[indices[0]] + indices[inp._ragged_idx]
    func_indices = (
        # before ragged dim
        indices[1 : inp._ragged_idx]
        # ragged dim (combined with batch)
        + [ragged_indices]
        # after ragged dim
        + indices[inp._ragged_idx + 1 :]
    )

    if func is torch.ops.aten.index_put_.default:
        inp._values = func(inp._values, func_indices, **new_kwargs)
        return inp

    return NestedTensor(
        func(inp._values, func_indices, **new_kwargs),
        **extract_kwargs(inp),
    )