def crd2crd(
    crd: IntTuple, dst_shape: IntTuple, src_shape: IntTuple | None = None
) -> IntTuple:
    if is_tuple(crd):
        if is_tuple(dst_shape):  # tuple tuple
            if len(crd) != len(dst_shape):
                raise AssertionError
            return tuple(crd2crd(x, y) for x, y in zip(crd, dst_shape))
        else:  # tuple "int"
            # Ambiguous unless we have src_shape
            if src_shape is None:
                raise AssertionError
            return crd2idx(crd, src_shape)
    else:
        if is_tuple(dst_shape):  # "int" tuple
            return idx2crd(crd, dst_shape)
        else:  # "int" "int"
            if crd >= dst_shape:
                raise AssertionError
            return crd