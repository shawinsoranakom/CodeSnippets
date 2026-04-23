def expand_condition_shorthand(value: Any | None) -> Any:
    """Expand boolean condition shorthand notations."""

    if not isinstance(value, dict) or CONF_CONDITIONS in value:
        return value

    for key, schema in (
        ("and", AND_CONDITION_SHORTHAND_SCHEMA),
        ("or", OR_CONDITION_SHORTHAND_SCHEMA),
        ("not", NOT_CONDITION_SHORTHAND_SCHEMA),
    ):
        try:
            schema(value)
            return {
                CONF_CONDITION: key,
                CONF_CONDITIONS: value[key],
                **{k: value[k] for k in value if k != key},
            }
        except vol.MultipleInvalid:
            pass

    if isinstance(value.get(CONF_CONDITION), list):
        try:
            CONDITION_SHORTHAND_SCHEMA(value)
            return {
                CONF_CONDITION: "and",
                CONF_CONDITIONS: value[CONF_CONDITION],
                **{k: value[k] for k in value if k != CONF_CONDITION},
            }
        except vol.MultipleInvalid:
            pass

    return value