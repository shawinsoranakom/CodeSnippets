def broadcast_tuples(
    left: Tuple | List, right: Tuple | List
) -> tuple[tuple[DType, ...], tuple[DType, ...]]:
    largs: tuple[DType, ...]
    rargs: tuple[DType, ...]
    if isinstance(left, List) and isinstance(right, List):
        largs = (left.wrapped,)
        rargs = (right.wrapped,)
    elif isinstance(left, List):
        assert isinstance(right, Tuple)
        assert not isinstance(right.args, EllipsisType)
        rargs = right.args
        largs = tuple(left.wrapped for _arg in rargs)
    elif isinstance(right, List):
        assert isinstance(left, Tuple)
        assert not isinstance(left.args, EllipsisType)
        largs = left.args
        rargs = tuple(right.wrapped for _arg in largs)
    else:
        assert isinstance(left, Tuple)
        assert isinstance(right, Tuple)
        assert not isinstance(left.args, EllipsisType)
        assert not isinstance(right.args, EllipsisType)
        largs = left.args
        rargs = right.args
    return (largs, rargs)