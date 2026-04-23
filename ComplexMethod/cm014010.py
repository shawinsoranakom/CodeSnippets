def is_from_defaults(source: Source) -> bool:
    if isinstance(source, DefaultsSource):
        return True

    # Accessed with func.__kwdefaults__["foo"]
    if (
        isinstance(source, DictGetItemSource)
        and isinstance(source.base, AttrSource)
        and source.base.member == "__kwdefaults__"
    ):
        return True

    # Accessed with func.__defaults__[0]
    if (
        isinstance(source, GetItemSource)
        and isinstance(source.base, AttrSource)
        and source.base.member == "__defaults__"
    ):
        return True

    if isinstance(source, ChainedSource):
        return is_from_defaults(source.base)
    return False