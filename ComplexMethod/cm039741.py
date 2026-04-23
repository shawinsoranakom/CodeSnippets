def count_nonzero(
    x: Array,
    /,
    *,
    axis: int | tuple[int, ...] | None = None,
    keepdims: bool = False,
) -> Array:
    result = torch.count_nonzero(x, dim=axis)
    if keepdims:
        if isinstance(axis, int):
            return result.unsqueeze(axis)
        elif isinstance(axis, tuple):
            n_axis = [x.ndim + ax if ax < 0 else ax for ax in axis]
            sh = [1 if i in n_axis else x.shape[i] for i in range(x.ndim)]
            return torch.reshape(result, sh)
        return _axis_none_keepdims(result, x.ndim, keepdims)
    else:
        return result