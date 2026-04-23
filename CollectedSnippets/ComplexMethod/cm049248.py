def clean_action(action, env):
    action_type = action.setdefault('type', 'ir.actions.act_window_close')
    if action_type == 'ir.actions.act_window' and not action.get('views'):
        generate_views(action)

    # When returning an action, keep only relevant fields/properties
    readable_fields = env[action['type']]._get_readable_fields()
    action_type_fields = env[action['type']]._fields.keys()

    cleaned_action = {
        field: value
        for field, value in action.items()
        # keep allowed fields and custom properties fields
        if field in readable_fields or field not in action_type_fields
    }

    # Warn about custom properties fields, because use is discouraged
    action_name = action.get('name') or action
    custom_properties = action.keys() - readable_fields - action_type_fields
    if custom_properties:
        _logger.warning("Action %r contains custom properties %s. Passing them "
            "via the `params` or `context` properties is recommended instead",
            action_name, ', '.join(map(repr, custom_properties)))

    return cleaned_action