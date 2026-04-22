def _get_default_count(default: Union[Sequence[Any], Any, None]) -> int:
    if default is None:
        return 0
    if not is_iterable(default):
        return 1
    return len(cast(Sequence[Any], default))