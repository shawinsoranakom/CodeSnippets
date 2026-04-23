def idx2crd(idx: IntTuple, shape: IntTuple, stride: IntTuple | None = None) -> IntTuple:
    if stride is None:
        stride = suffix_product(shape)

    if is_tuple(idx):
        if is_tuple(shape) and is_tuple(stride):  # tuple tuple tuple
            if not (len(idx) == len(shape) and len(stride) == len(shape)):
                raise AssertionError
            return tuple(idx2crd(i, s, d) for i, s, d in zip(idx, shape, stride))
        else:  # tuple "int" "int"
            raise AssertionError("Invalid combination: tuple with int stride")
    else:
        if is_tuple(shape) and is_tuple(stride):  # "int" tuple tuple
            if len(shape) != len(stride):
                raise AssertionError
            return tuple(idx2crd(idx, s, d) for s, d in zip(shape, stride))
        else:  # "int" "int" "int"
            if is_tuple(shape) or is_tuple(stride):
                raise AssertionError
            return (idx // stride) % shape