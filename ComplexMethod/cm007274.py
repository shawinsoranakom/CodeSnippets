def set_current_fields(
    build_config: dotdict,
    action_fields: dict[str, list[str]],
    *,
    selected_action: str | None = None,
    default_fields: list[str] = DEFAULT_FIELDS,
    func: Callable = set_field_display,
    default_value: bool | None = None,
) -> dotdict:
    """Set the current fields for a selected action."""
    # action_fields = {action1: [field1, field2], action2: [field3, field4]}
    # we need to show action of one field and disable the rest
    if default_value is None:
        default_value = False

    def _call_func(build_config: dotdict, field: str, *, value: bool) -> dotdict:
        """Helper to call the function with appropriate signature."""
        if func == set_field_advanced:
            return func(build_config, field, value=value)
        return func(build_config, field, value)

    if selected_action in action_fields:
        for field in action_fields[selected_action]:
            build_config = _call_func(build_config, field, value=not default_value)
        for key, value in action_fields.items():
            if key != selected_action:
                for field in value:
                    build_config = _call_func(build_config, field, value=default_value)
    if selected_action is None:
        for value in action_fields.values():
            for field in value:
                build_config = _call_func(build_config, field, value=default_value)
    if default_fields is not None:
        for field in default_fields:
            build_config = _call_func(build_config, field, value=not default_value)
    return build_config