def result_type(*arrays_and_dtypes: Array | DType | complex) -> DType:
    num = len(arrays_and_dtypes)

    if num == 0:
        raise ValueError("At least one array or dtype must be provided")

    elif num == 1:
        x = arrays_and_dtypes[0]
        if isinstance(x, torch.dtype):
            return x
        return x.dtype

    if num == 2:
        x, y = arrays_and_dtypes
        return _result_type(x, y)

    else:
        # sort scalars so that they are treated last
        scalars, others = [], []
        for x in arrays_and_dtypes:
            if isinstance(x, _py_scalars):
                scalars.append(x)
            else:
                others.append(x)
        if not others:
            raise ValueError("At least one array or dtype must be provided")

        # combine left-to-right
        return _reduce(_result_type, others + scalars)