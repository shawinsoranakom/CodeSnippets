def broadcast_shapes(shape1, shape2):
    if len(shape1) <= 0:
        raise AssertionError(f"shape1 must have length > 0, got {len(shape1)}")
    if len(shape2) <= 0:
        raise AssertionError(f"shape2 must have length > 0, got {len(shape2)}")
    s1 = list(shape1)
    s2 = list(shape2)
    # TODO: Support non-equal-rank broadcast where semantics match.
    # This can be tricky for NHWC tensors because dimension orders
    # don't match between PT and NNAPI, even though semantics match.
    if len(s1) > len(s2):
        # s2 = [1] * (len(s1) - len(s2)) + s2
        raise Exception(  # noqa: TRY002
            "Non-equal-rank broadcast is not supported yet."
        )
    if len(s2) > len(s1):
        # s3 = [1] * (len(s2) - len(s1)) + s1
        raise Exception(  # noqa: TRY002
            "Non-equal-rank broadcast is not supported yet."
        )
    ret = []
    for d1, d2 in zip(s1, s2):
        if d1 == 1:
            ret.append(d2)
        elif d2 == 1:
            ret.append(d1)
        elif d1 == d2:
            ret.append(d1)
        else:
            raise Exception(  # noqa: TRY002
                f"Cannot broadcast shapes: {shape1} and {shape2}"
            )
    return tuple(ret)