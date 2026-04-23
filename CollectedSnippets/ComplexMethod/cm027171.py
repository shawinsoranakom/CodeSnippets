def get_schema(prop, name, groups):
    """Return the correct schema type."""
    if prop.is_read_only:
        return _read_only_schema(name, prop.value)
    if name == RAMP_RATE_IN_SEC:
        return _list_schema(name, RAMP_RATE_LIST)
    if name == RADIO_BUTTON_GROUPS:
        button_list = {str(group): groups[group].name for group in groups}
        return _multi_select_schema(name, button_list)
    if name == LOAD_BUTTON:
        button_list = {group: groups[group].name for group in groups}
        return _list_schema(name, button_list)
    if prop.value_type is bool:
        return _bool_schema(name)
    if prop.value_type is int:
        return _byte_schema(name)
    if prop.value_type is float:
        return _float_schema(name)
    if prop.value_type == ToggleMode:
        return _list_schema(name, TOGGLE_MODES)
    if prop.value_type == RelayMode:
        return _list_schema(name, RELAY_MODES)
    return None