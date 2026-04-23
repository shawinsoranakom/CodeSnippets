def _result_type(x: Array | DType | complex, y: Array | DType | complex) -> DType:
    if not (isinstance(x, _py_scalars) or isinstance(y, _py_scalars)):
        xdt = x if isinstance(x, torch.dtype) else x.dtype
        ydt = y if isinstance(y, torch.dtype) else y.dtype

        try:
            return _promotion_table[xdt, ydt]
        except KeyError:
            pass

    # This doesn't result_type(dtype, dtype) for non-array API dtypes
    # because torch.result_type only accepts tensors. This does however, allow
    # cross-kind promotion.
    x = torch.tensor([], dtype=x) if isinstance(x, torch.dtype) else x
    y = torch.tensor([], dtype=y) if isinstance(y, torch.dtype) else y
    return torch.result_type(x, y)