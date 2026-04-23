def event_callback(event):
        """Handle incoming Rflink events.

        Rflink events arrive as dictionaries of varying content
        depending on their type. Identify the events and distribute
        accordingly.
        """
        event_type = identify_event_type(event)
        _LOGGER.debug("event of type %s: %s", event_type, event)

        # Don't propagate non entity events (eg: version string, ack response)
        if event_type not in hass.data[DATA_ENTITY_LOOKUP]:
            _LOGGER.debug("unhandled event of type: %s", event_type)
            return

        # Lookup entities who registered this device id as device id or alias
        event_id = event.get(EVENT_KEY_ID)

        is_group_event = (
            event_type == EVENT_KEY_COMMAND
            and event[EVENT_KEY_COMMAND] in RFLINK_GROUP_COMMANDS
        )
        if is_group_event:
            entity_ids = hass.data[DATA_ENTITY_GROUP_LOOKUP][event_type].get(
                event_id, []
            )
        else:
            entity_ids = hass.data[DATA_ENTITY_LOOKUP][event_type][event_id]

        _LOGGER.debug("entity_ids: %s", entity_ids)
        if entity_ids:
            # Propagate event to every entity matching the device id
            for entity in entity_ids:
                _LOGGER.debug("passing event to %s", entity)
                async_dispatcher_send(hass, SIGNAL_HANDLE_EVENT.format(entity), event)
        elif not is_group_event:
            # If device is not yet known, register with platform (if loaded)
            if event_type in hass.data[DATA_DEVICE_REGISTER]:
                _LOGGER.debug("device_id not known, adding new device")
                # Add bogus event_id first to avoid race if we get another
                # event before the device is created
                # Any additional events received before the device has been
                # created will thus be ignored.
                hass.data[DATA_ENTITY_LOOKUP][event_type][event_id].append(
                    TMP_ENTITY.format(event_id)
                )
                hass.async_create_task(
                    hass.data[DATA_DEVICE_REGISTER][event_type](event),
                    eager_start=False,
                )
            else:
                _LOGGER.debug("device_id not known and automatic add disabled")