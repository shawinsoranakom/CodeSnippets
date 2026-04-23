def _index_fill(
    x: TensorLike,
    dim: int,
    index: TensorLike,
    value: NumberType | TensorLike,
    *,
    inplace: bool,
):
    torch._check(
        index.ndim <= 1,
        lambda: f"Index should have dimension 1 or 0 (got {index.ndim})",
    )
    if isinstance(value, TensorLike):
        torch._check(
            value.ndim == 0,
            lambda: "Only supports 0-dimensional value tensor. "  # type: ignore[union-attr]
            f"Got a tensor with {value.ndim} dimensions.",
        )  # type: ignore[arg-type]
    else:
        value = torch.scalar_tensor(
            value,
            dtype=x.dtype,
            layout=x.layout,
            device=x.device,  # type: ignore[arg-type]
        )

    # index_copy has some unnecessary preconditions when x is a scalar. We do this to work through them
    zero_dim = x.ndim == 0
    y = x.unsqueeze(0) if zero_dim else x
    # index_copy does not broadcast on value so we have to do it manually
    shape = list(y.shape)
    shape[dim] = index.numel()
    value = value.expand(shape)
    index_copy = Tensor.index_copy_ if inplace else torch.index_copy
    out = index_copy(y, dim, index, value)  # type: ignore[operator]
    if inplace:
        return x
    else:
        if zero_dim:
            # The clone is necessary so that it returns a fresh tensor rather than a view
            out = out.squeeze(0).clone()
        # index_fill preserves the strides for non-overlapping-and-dense inputs
        # (matching clone(Preserve) behavior). index_copy always returns contiguous tensors.
        if out.stride() != x.stride() and utils.is_non_overlapping_and_dense_or_false(
            x
        ):
            out = prims.copy_strided(out, x.stride())
        return out