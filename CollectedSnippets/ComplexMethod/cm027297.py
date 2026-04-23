def _replace_all_abbreviations(
    discovery_payload: dict[str, Any], component_only: bool = False
) -> None:
    """Replace all abbreviations in an MQTT discovery payload."""

    _replace_abbreviations(discovery_payload, ABBREVIATIONS, ABBREVIATIONS_SET)

    if CONF_AVAILABILITY in discovery_payload:
        for availability_conf in cv.ensure_list(discovery_payload[CONF_AVAILABILITY]):
            _replace_abbreviations(availability_conf, ABBREVIATIONS, ABBREVIATIONS_SET)

    if component_only:
        return

    if CONF_ORIGIN in discovery_payload:
        _replace_abbreviations(
            discovery_payload[CONF_ORIGIN],
            ORIGIN_ABBREVIATIONS,
            ORIGIN_ABBREVIATIONS_SET,
        )

    if CONF_DEVICE in discovery_payload:
        _replace_abbreviations(
            discovery_payload[CONF_DEVICE],
            DEVICE_ABBREVIATIONS,
            DEVICE_ABBREVIATIONS_SET,
        )

    if CONF_COMPONENTS in discovery_payload:
        if not isinstance(discovery_payload[CONF_COMPONENTS], dict):
            return
        for comp_conf in discovery_payload[CONF_COMPONENTS].values():
            _replace_all_abbreviations(comp_conf, component_only=True)