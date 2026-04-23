def async_replace_list_data(
    data: list | set | tuple, to_replace: dict[str, str]
) -> list[Any]:
    """Redact sensitive data in a list."""
    redacted = []
    for item in data:
        new_value: Any | None = None
        if isinstance(item, (list, set, tuple)):
            new_value = async_replace_list_data(item, to_replace)
        elif isinstance(item, Mapping):
            new_value = async_replace_dict_data(item, to_replace)
        elif isinstance(item, str):
            if item in to_replace:
                new_value = to_replace[item]
            elif item.count(":") == 5:
                new_value = REDACTED
        redacted.append(new_value or item)
    return redacted