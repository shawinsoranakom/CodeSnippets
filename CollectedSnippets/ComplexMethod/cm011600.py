def squeeze(a: TensorLikeType, dim: DimsType | None = None) -> TensorLikeType:
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if dim is None:
        dims = tuple(idx for idx, size in enumerate(a.shape) if size == 1)
        return prims.squeeze(a, dims) if dims else prims.view_of(a)

    ndim = a.ndim

    dim = utils.canonicalize_dims(ndim, dim)
    dims = (dim,) if isinstance(dim, Dim) else dim
    # Short-circuits if the tensor has no dimensions
    if ndim == 0:
        if not (len(dims) == 0 or dims == (0,)):
            raise AssertionError(
                f"Expected dims to be empty or (0,) for 0-dim tensor, got {dims}"
            )
        return prims.view_of(a)

    # Note: squeeze does not modify tensors when the given dim is not a dimension of length 1
    # would it be better if we just not allow 1 for unbacked at runtiume?
    dims = tuple(d for d in dims if guard_or_false(a.shape[d] == 1))
    if len(dims) == 0:
        return prims.view_of(a)
    if len(dims) == 1:
        return prims.squeeze(a, dims)
    dims_list = list(dims)
    dims_list = sorted(dims_list, reverse=True)
    for i in dims_list:
        a = squeeze(a, i)
    return a