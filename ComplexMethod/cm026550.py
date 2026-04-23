def _check_host_port_alias_match(
    first: Mapping[str, Any], second: Mapping[str, Any]
) -> bool:
    """Check if first and second have the same host, port and alias."""

    if first[CONF_HOST] != second[CONF_HOST] or first[CONF_PORT] != second[CONF_PORT]:
        return False

    first_alias = first.get(CONF_ALIAS)
    second_alias = second.get(CONF_ALIAS)
    if (first_alias is None and second_alias is None) or (
        first_alias is not None
        and second_alias is not None
        and first_alias == second_alias
    ):
        return True

    return False