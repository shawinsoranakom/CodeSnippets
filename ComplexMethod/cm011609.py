def _infer_scalar_type(obj):
    if isinstance(obj, FloatLike):
        return torch.get_default_dtype()
    if isinstance(obj, IntLike) and not isinstance(obj, bool):  # careful!
        return torch.int64
    if isinstance(obj, BoolLike):
        return torch.bool
    if isinstance(obj, complex):
        default_dtype = torch.get_default_dtype()
        if default_dtype is torch.float:
            return torch.cfloat
        elif default_dtype is torch.double:
            return torch.cdouble
        elif default_dtype is torch.half:
            return torch.chalf
        else:
            raise RuntimeError("invalid default scalar type for complex")
    if isinstance(obj, torch.Tensor):
        return obj.dtype
    if isinstance(obj, str):
        raise TypeError(f"new(): invalid data type '{type(obj).__name__}'")
    # TODO: this is inaccurate, we actually test PySequence_Check
    if isinstance(obj, (list, tuple)):
        scalarType = None
        length = len(obj)
        # match NumPy semantics, except use default tensor type instead of
        # double.
        if length == 0:
            return torch.get_default_dtype()

        for i in range(length):
            cur_item = obj[i]
            # TODO: test this
            """
            if cur_item is obj:
                raise TypeError("new(): self-referential lists are incompatible")
            """
            item_scalarType = _infer_scalar_type(cur_item)  # recurse!
            if scalarType is not None:
                scalarType = torch.promote_types(scalarType, item_scalarType)
            else:
                scalarType = item_scalarType
            if scalarType is torch.cdouble:
                # this won't change (unless we hit undefined, but that will
                # fail later)
                return scalarType
        return scalarType
    raise RuntimeError(f"Could not infer dtype of {type(obj).__name__}")