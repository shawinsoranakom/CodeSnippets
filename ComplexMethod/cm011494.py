def dim_reduction(ndim: int, dim_or_dims: DimsType | None, keepdim: bool) -> DimMap:
    """
    General fallback for reduction ops where Partial() does not apply.

    This will cause incoming tensor to be replicated on the reducing dimensions.
    """
    if dim_or_dims is None:
        dim_or_dims = tuple(range(ndim))
    if isinstance(dim_or_dims, int):
        dim_or_dims = (dim_or_dims,)
    dim_or_dims = tuple(d if d >= 0 else d + ndim for d in dim_or_dims)
    return tuple(
        InputDim(i) if i not in dim_or_dims else Singleton()
        for i in range(ndim)
        if i not in dim_or_dims or keepdim
    )