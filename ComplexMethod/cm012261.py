def _other_is_broadcasted_in_dim(match):
    # Check that the scaling factor is constant across the reduction dim,
    # so scaling doesn't change which index corresponds to the maximum value
    other = match.kwargs["other"]
    if isinstance(other, (int, float)):
        return True

    inp = match.kwargs["inp"]
    if not all(isinstance(x, torch.fx.Node) for x in (inp, other)):
        return False

    inp_example = inp.meta["val"]
    other_example = other.meta["val"]
    if isinstance(other_example, (torch.SymInt, torch.SymFloat)):
        return True

    if not all(isinstance(x, torch.Tensor) for x in (inp_example, other_example)):
        return False

    inp_ndim = inp_example.ndim
    other_shape = other_example.shape
    if inp_ndim < len(other_shape):
        return False

    # Pad other_shape to the same ndim as inp
    other_shape = [1] * (inp_ndim - len(other_shape)) + list(other_shape)

    dim = match.kwargs["dim"]
    if isinstance(dim, int):
        dim = (dim,)

    if any(d >= len(other_shape) for d in dim):
        return False

    return all(statically_known_true(other_shape[d] == 1) for d in dim)