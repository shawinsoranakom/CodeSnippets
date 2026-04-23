def dtype_issubclass(
    left: DType, right: DType, *, int_float_compatible: bool = True
) -> bool:
    if right == ANY:  # catch the case, when left=Optional[T] and right=Any
        return True
    elif isinstance(left, Optional):
        if isinstance(right, Optional):
            return dtype_issubclass(
                unoptionalize(left),
                unoptionalize(right),
                int_float_compatible=int_float_compatible,
            )
        else:
            return False
    elif left == NONE:
        return isinstance(right, Optional) or right == NONE
    elif isinstance(right, Optional):
        return dtype_issubclass(
            left, unoptionalize(right), int_float_compatible=int_float_compatible
        )
    elif isinstance(left, (Tuple, List)) and isinstance(right, (Tuple, List)):
        return dtype_tuple_issubclass(
            left, right, int_float_compatible=int_float_compatible
        )
    elif isinstance(left, Array) and isinstance(right, Array):
        return dtype_array_equivalence(left, right)
    elif isinstance(left, Pointer) and isinstance(right, Pointer):
        return dtype_pointer_issubclass(left, right)
    elif isinstance(left, _SimpleDType) and isinstance(right, _SimpleDType):
        if left == INT and right == FLOAT:
            return int_float_compatible
        elif left == BOOL and right == INT:
            return False
        else:
            return issubclass(left.wrapped, right.wrapped)
    elif isinstance(left, Callable) and isinstance(right, Callable):
        return True
    return left == right