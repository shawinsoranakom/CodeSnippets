def async_describe_deconz_event(event: Event) -> dict[str, str]:
        """Describe deCONZ logbook event."""
        if device := device_registry.devices.get(event.data[ATTR_DEVICE_ID]):
            deconz_event = _get_deconz_event_from_device(hass, device)
            name = deconz_event.device.name
        else:
            deconz_event = None
            name = event.data[CONF_ID]

        action = None
        interface = None
        data = event.data.get(CONF_EVENT) or event.data.get(CONF_GESTURE, "")

        if data and deconz_event and deconz_event.device.model_id in REMOTES:
            action, interface = _get_device_event_description(
                deconz_event.device.model_id, data
            )

        # Unknown event
        if not data:
            return {
                LOGBOOK_ENTRY_NAME: name,
                LOGBOOK_ENTRY_MESSAGE: "fired an unknown event",
            }

        # No device event match
        if not action:
            return {
                LOGBOOK_ENTRY_NAME: name,
                LOGBOOK_ENTRY_MESSAGE: f"fired event '{data}'",
            }

        # Gesture event
        if not interface:
            return {
                LOGBOOK_ENTRY_NAME: name,
                LOGBOOK_ENTRY_MESSAGE: f"fired event '{ACTIONS[action]}'",
            }

        return {
            LOGBOOK_ENTRY_NAME: name,
            LOGBOOK_ENTRY_MESSAGE: (
                f"'{ACTIONS[action]}' event for '{INTERFACES[interface]}' was fired"
            ),
        }