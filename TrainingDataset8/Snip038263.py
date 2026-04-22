def is_iterable(obj: object) -> TypeGuard[Iterable[Any]]:
    try:
        # The ignore statement here is intentional, as this is a
        # perfectly fine way of checking for iterables.
        iter(obj)  # type: ignore[call-overload]
    except TypeError:
        return False
    return True