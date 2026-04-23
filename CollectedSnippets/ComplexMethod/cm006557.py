def set_current_fields(
    build_config: dotdict,
    action_fields: dict[str, list[str]],
    selected_action: str | None = None,
    default_fields: list[str] = DEFAULT_FIELDS,
    func: Callable[[dotdict, str, bool], dotdict] = set_field_display,
    *,
    default_value: bool | None = None,
) -> dotdict:
    """Set the current fields for a selected action."""
    # action_fields = {action1: [field1, field2], action2: [field3, field4]}
    # we need to show action of one field and disable the rest
    if default_value is None:
        default_value = False
    if selected_action in action_fields:
        for field in action_fields[selected_action]:
            build_config = func(build_config, field, not default_value)
        for key, value in action_fields.items():
            if key != selected_action:
                for field in value:
                    build_config = func(build_config, field, default_value)
    if selected_action is None:
        for value in action_fields.values():
            for field in value:
                build_config = func(build_config, field, default_value)
    if default_fields is not None:
        for field in default_fields:
            build_config = func(build_config, field, not default_value)
    return build_config