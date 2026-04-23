def reference_flatten(input, start_dim=0, end_dim=-1):
    in_shape = input.shape
    in_rank = len(in_shape)
    for d in start_dim, end_dim:
        if not ((in_rank == 0 and d in (-1, 0)) or -in_rank <= d < in_rank):
            raise IndexError(f"Dimension out of range (expected to be in range of [{-in_rank}, {in_rank - 1}], but got {d}")
    end_dim = end_dim if end_dim >= 0 else in_rank + end_dim
    start_dim = start_dim if start_dim >= 0 else in_rank + start_dim
    if in_rank == 0:
        end_dim = start_dim
    if end_dim < start_dim:
        raise RuntimeError("flatten() has invalid args: start_dim cannot come after end_dim")
    flatten_bit_dim = functools.reduce(operator.mul, in_shape[start_dim:end_dim + 1], 1)
    out_shape = in_shape[:start_dim] + (flatten_bit_dim,) + in_shape[end_dim + 1:]
    return np.reshape(input, out_shape)