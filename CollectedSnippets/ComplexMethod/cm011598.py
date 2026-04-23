def roll(a: TensorLikeType, shifts: DimsType, dims: DimsType = ()) -> TensorLikeType:
    """Reference implementation of :func:`torch.roll`."""

    dims = utils.canonicalize_dims(a.ndim, dims)
    # ATen specifies int[1] type for shifts and dims which expands integers to tuples of length 1
    if not isinstance(shifts, Iterable):
        shifts = (shifts,)
    if not isinstance(dims, Iterable):
        dims = (dims,)

    # Avoid modulo by zero
    if a.numel() == 0:
        # Keeping this as ref for now as FakeTensor runs into some issues with complex tensors
        return a.clone()

    # pyrefly: ignore [bad-argument-type]
    if a.dim() == 0 and len(dims) > 0:
        raise IndexError(
            # pyrefly: ignore [bad-index, index-error]
            f"Dimension specified as {dims[0]} but tensor has no dimensions"
        )

    # pyrefly: ignore [bad-argument-type]
    len_shifts = len(shifts)
    # pyrefly: ignore [bad-argument-type]
    len_dims = len(dims)
    if len_shifts != 1 or len_dims != 1:
        if len_shifts == 0:
            raise RuntimeError("`shifts` required")
        # Takes care of the case when dims is not specified (default)
        # By default, the tensor is flattened before shifting, after which the original shape is restored
        if len_dims == 0 and len_shifts == 1:
            return torch.roll(torch.flatten(a), shifts, 0).view(a.shape)
        if len_shifts != len_dims:
            raise RuntimeError(
                f"shifts and dimensions must align. shifts: {len_shifts}, dims: {len_dims}"
            )
        if len_dims <= 1:
            raise AssertionError(f"Expected len_dims > 1, got {len_dims}")
        # pyrefly: ignore [bad-index]
        tail_shifts = shifts[1:]
        # pyrefly: ignore [bad-index, index-error]
        tail_dims = dims[1:]
        # pyrefly: ignore [bad-index, index-error]
        # pyrefly: ignore [bad-index, index-error]
        first_dim_rolled = torch.roll(a, (shifts[0],), dims[0])
        return torch.roll(first_dim_rolled, tail_shifts, tail_dims)

    # This path is taken when only one dimension is rolled
    # For example to get `first_dim_rolled` above
    # pyrefly: ignore [bad-index, index-error]
    dim = dims[0]
    size = a.shape[dim]
    # pyrefly: ignore [bad-index, index-error]
    start = (size - shifts[0]) % size
    idx = torch.arange(size, device=a.device)
    return a.index_select(dim, torch.fmod(start + idx, size))