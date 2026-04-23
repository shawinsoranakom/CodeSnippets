def flatten(input: list[int], start_dim: int, end_dim: int):
    start_dim = maybe_wrap_dim(start_dim, len(input))
    end_dim = maybe_wrap_dim(end_dim, len(input))
    if start_dim > end_dim:
        raise AssertionError(f"Expected start_dim ({start_dim}) <= end_dim ({end_dim})")
    if len(input) == 0:
        return [1]
    if start_dim == end_dim:
        # TODO: return self
        out: list[int] = []
        for elem in input:
            out.append(elem)
        return out
    slice_numel = 1
    for i in range(start_dim, end_dim + 1):
        slice_numel *= input[i]
    # TODO: use slicing when slice optimization has landed
    # slice_numel = multiply_integers(input[start_dim:end_dim - start_dim + 1])
    shape: list[int] = []
    for i in range(start_dim):
        shape.append(input[i])
    shape.append(slice_numel)
    for i in range(end_dim + 1, len(input)):
        shape.append(input[i])
    return shape