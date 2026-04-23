def _validate_zone_input(zone_input: dict[str, Any] | None) -> dict[str, str]:
    if not zone_input:
        return {}
    errors = {}

    # CONF_RELAY_ADDR & CONF_RELAY_CHAN are inclusive
    if (CONF_RELAY_ADDR in zone_input and CONF_RELAY_CHAN not in zone_input) or (
        CONF_RELAY_ADDR not in zone_input and CONF_RELAY_CHAN in zone_input
    ):
        errors["base"] = "relay_inclusive"

    # The following keys must be int
    for key in (CONF_ZONE_NUMBER, CONF_ZONE_LOOP, CONF_RELAY_ADDR, CONF_RELAY_CHAN):
        if key in zone_input:
            try:
                int(zone_input[key])
            except ValueError:
                errors[key] = "int"

    # CONF_ZONE_LOOP depends on CONF_ZONE_RFID
    if CONF_ZONE_LOOP in zone_input and CONF_ZONE_RFID not in zone_input:
        errors[CONF_ZONE_LOOP] = "loop_rfid"

    # CONF_ZONE_LOOP must be 1-4
    if (
        CONF_ZONE_LOOP in zone_input
        and zone_input[CONF_ZONE_LOOP].isdigit()
        and int(zone_input[CONF_ZONE_LOOP]) not in list(range(1, 5))
    ):
        errors[CONF_ZONE_LOOP] = "loop_range"

    return errors