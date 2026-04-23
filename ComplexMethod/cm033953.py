def detect_profile_name(value: str) -> str:
    """
    Detect (optional) JSON profile name from an inventory JSON document.
    Defaults to `inventory_legacy`.
    """
    try:
        data = json.loads(value)
    except Exception as ex:
        raise ValueError('Value could not be parsed as JSON.') from ex

    if not isinstance(data, dict):
        raise TypeError(f'Value is {native_type_name(data)!r} instead of {native_type_name(dict)!r}.')

    if (meta := data.get('_meta', ...)) is ...:
        return _inventory_legacy.Decoder.profile_name

    if not isinstance(meta, dict):
        raise TypeError(f"Value contains '_meta' which is {native_type_name(meta)!r} instead of {native_type_name(dict)!r}.")

    if (profile := meta.get('profile', ...)) is ...:
        return _inventory_legacy.Decoder.profile_name

    if not isinstance(profile, str):
        raise TypeError(f"Value contains '_meta.profile' which is {native_type_name(profile)!r} instead of {native_type_name(str)!r}.")

    if not profile.startswith('inventory_'):
        raise ValueError(f"Non-inventory profile {profile!r} is not allowed.")

    return profile