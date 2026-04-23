def _canonical_dim(dim: DimOrDims, ndim: int) -> tuple[int, ...]:
    """Return dim argument as a tuple of sorted dim values."""
    dims: list[int] = []
    if dim == ():
        # Currently, `dim=()` in reductions operations means "reduce
        # over all dimensions" while in future, it will read "no
        # reduce". See https://github.com/pytorch/pytorch/issues/29137
        # When gh-29137 is resolved, this if-block must be deleted.
        dim = None
    if dim is None:
        return tuple(range(ndim))
    ndim = max(ndim, 1)
    dim_ = (dim,) if isinstance(dim, (int, torch.SymInt)) else dim
    for d in dim_:
        if d in dims:
            raise RuntimeError(f"dim={d} appears multiple times in the list of dims")
        if d >= ndim or d < -ndim:
            raise IndexError(
                f"Dimension out of range (expected to be in range of [{-ndim}, {ndim - 1}], but got {d})"
            )
        # pyrefly: ignore [bad-argument-type]
        dims.append(d % ndim)
    return tuple(sorted(dims))