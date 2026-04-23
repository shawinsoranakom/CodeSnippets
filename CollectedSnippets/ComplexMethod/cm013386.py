def array(obj, dtype=None, *, copy=True, order="K", subok=False, ndmin=0, like=None):
    if subok is not False:
        raise NotImplementedError("'subok' parameter is not supported.")
    if like is not None:
        raise NotImplementedError("'like' parameter is not supported.")
    if order != "K":
        raise NotImplementedError

    # a happy path
    if (
        isinstance(obj, ndarray)
        and copy is False
        and dtype is None
        and ndmin <= obj.ndim
    ):
        return obj

    if isinstance(obj, (list, tuple)):
        # FIXME and they have the same dtype, device, etc
        if obj and all(isinstance(x, torch.Tensor) for x in obj):
            # list of arrays: *under torch.Dynamo* these are FakeTensors
            obj = torch.stack(obj)
        else:
            # XXX: remove tolist
            # lists of ndarrays: [1, [2, 3], ndarray(4)] convert to lists of lists
            obj = _tolist(obj)

    # is obj an ndarray already?
    if isinstance(obj, ndarray):
        obj = obj.tensor

    # is a specific dtype requested?
    torch_dtype = None
    if dtype is not None:
        torch_dtype = _dtypes.dtype(dtype).torch_dtype

    tensor = _util._coerce_to_tensor(obj, torch_dtype, copy, ndmin)
    return ndarray(tensor)