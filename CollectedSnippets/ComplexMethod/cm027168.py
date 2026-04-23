def async_fire_insteon_event(
        name: str, address: Address, group: int, button: str | None = None
    ):
        # Firing an event when a button is pressed.
        if button and button[-2] == "_":
            button_id = button[-1].lower()
        else:
            button_id = None

        schema = {CONF_ADDRESS: address, "group": group}
        if button_id:
            schema[EVENT_CONF_BUTTON] = button_id
        if name == ON_EVENT:
            event = EVENT_GROUP_ON
        elif name == OFF_EVENT:
            event = EVENT_GROUP_OFF
        elif name == ON_FAST_EVENT:
            event = EVENT_GROUP_ON_FAST
        elif name == OFF_FAST_EVENT:
            event = EVENT_GROUP_OFF_FAST
        else:
            event = f"insteon.{name}"
        _LOGGER.debug("Firing event %s with %s", event, schema)
        hass.bus.async_fire(event, schema)