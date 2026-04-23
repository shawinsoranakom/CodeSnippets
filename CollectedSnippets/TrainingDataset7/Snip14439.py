def sanitize_separators(value):
    """
    Sanitize a value according to the current decimal and
    thousand separator setting. Used with form field input.
    """
    if isinstance(value, str):
        parts = []
        decimal_separator = get_format("DECIMAL_SEPARATOR")
        if decimal_separator in value:
            value, decimals = value.split(decimal_separator, 1)
            parts.append(decimals)
        if settings.USE_THOUSAND_SEPARATOR:
            thousand_sep = get_format("THOUSAND_SEPARATOR")
            if (
                thousand_sep == "."
                and value.count(".") == 1
                and len(value.split(".")[-1]) != 3
            ):
                # Special case where we suspect a dot meant decimal separator
                # (see #22171).
                pass
            else:
                for replacement in {
                    thousand_sep,
                    unicodedata.normalize("NFKD", thousand_sep),
                }:
                    value = value.replace(replacement, "")
        parts.append(value)
        value = ".".join(reversed(parts))
    return value