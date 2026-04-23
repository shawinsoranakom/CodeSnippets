def crd2idx(
    crd: IntTuple | None, shape: IntTuple, stride: IntTuple | None = None
) -> int:
    if stride is None:
        stride = suffix_product(shape)

    if is_tuple(crd):
        if is_tuple(shape) and is_tuple(stride):  # tuple tuple tuple
            if not (len(crd) == len(shape) and len(stride) == len(shape)):
                raise AssertionError
            return sum(crd2idx(c, s, d) for c, s, d in zip(crd, shape, stride))
        else:  # tuple "int" "int"
            raise AssertionError(f"Invalid combination: crd={crd}, shape={shape}")
    else:
        if crd is None:
            crd = 0

        if is_tuple(shape) and is_tuple(stride):  # "int" tuple tuple
            if len(shape) != len(stride):
                raise AssertionError
            result = 0
            # Process from right to left for lexicographic ordering
            for i in range(len(shape) - 1, 0, -1):
                result += crd2idx(crd % product(shape[i]), shape[i], stride[i])
                crd = crd // product(shape[i])
            if len(shape) > 0:
                result += crd2idx(crd, shape[0], stride[0])
            return result
        else:  # "int" "int" "int"
            if is_tuple(shape) or is_tuple(stride):
                raise AssertionError
            return crd * stride