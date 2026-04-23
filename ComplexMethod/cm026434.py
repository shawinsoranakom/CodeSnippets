def format_migration_config(
    config: ConfigType | list[ConfigType], depth: int = 0
) -> ConfigType | list[ConfigType]:
    """Recursive method to format templates as strings from ConfigType."""
    if depth > 9:
        raise RecursionError

    if isinstance(config, list):
        items = []
        for item in config:
            if isinstance(item, (dict, list)):
                if len(item) > 0:
                    items.append(format_migration_config(item, depth + 1))
            else:
                items.append(_format_template(item))
        return items  # type: ignore[return-value]

    formatted_config = {}
    for field, value in config.items():
        if isinstance(value, dict):
            if len(value) > 0:
                formatted_config[field] = format_migration_config(value, depth + 1)
        elif isinstance(value, list):
            if len(value) > 0:
                formatted_config[field] = format_migration_config(value, depth + 1)
            else:
                formatted_config[field] = []
        elif isinstance(value, ScriptVariables):
            formatted_config[field] = format_migration_config(
                value.as_dict(), depth + 1
            )
        else:
            formatted_config[field] = _format_template(value)

    return formatted_config