def _value_or_dg(
    value: Union[None, Type[NoValue], Value],
    dg: DG,
) -> Union[DG, None, Value]:
    """Return either value, or None, or dg.

    This is needed because Widgets have meaningful return values. This is
    unlike other elements, which always return None. Then we internally replace
    that None with a DeltaGenerator instance.

    However, sometimes a widget may want to return None, and in this case it
    should not be replaced by a DeltaGenerator. So we have a special NoValue
    object that gets replaced by None.

    """
    if value is NoValue:
        return None
    if value is None:
        return dg
    return cast(Value, value)