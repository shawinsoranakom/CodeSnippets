def _index_add(
    x: TensorLike,
    dim: int,
    index: TensorLike,
    tensor: TensorLike,
    *,
    inplace: bool,
    alpha: NumberType = 1,
):
    dim = utils.canonicalize_dims(x.ndim, dim)
    torch._check(
        index.ndim <= 1,
        lambda: f"Index should have dimension 1 or 0 (got {index.ndim})",
    )
    index_size = index.size(0) if index.ndim == 1 else 1
    tensor_size = tensor.size(dim) if tensor.ndim > 0 else 1
    torch._check(
        tensor_size == index_size,
        lambda: f"Number of indices ({index_size}) should be equal to tensor.size(dim) ({tensor_size}), for {dim=}",
    )
    if alpha != 1:
        python_type = utils.dtype_to_type(x.dtype)
        torch._check(
            python_type is bool
            or utils.is_weakly_lesser_type(type(alpha), python_type),
            lambda: f"alpha argument of type {type(alpha)} cannot be safely cast to type {python_type}!",
        )
        tensor = tensor * alpha
    # Treat scalars as elements of \R^1
    zero_dim = x.ndim == 0
    x1 = x.unsqueeze(0) if zero_dim else x
    idx = (None,) * dim + (index,)
    index_put = aten.index_put_ if inplace else aten.index_put
    out = index_put(x1, idx, tensor, accumulate=True)
    if inplace:
        return x
    else:
        return out.squeeze(0) if zero_dim else out.contiguous()