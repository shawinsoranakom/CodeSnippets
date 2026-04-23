def _is_range_value(value: Union[T, Sequence[T]]) -> TypeGuard[Sequence[T]]:
    return isinstance(value, (list, tuple))