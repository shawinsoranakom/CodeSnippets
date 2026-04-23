def async_handle_receive(event: rfxtrxmod.RFXtrxEvent) -> None:
        """Handle received messages from RFXtrx gateway."""

        if isinstance(event, rfxtrxmod.ConnectionLost):
            _LOGGER.warning("Connection was lost, triggering reload")
            hass.async_create_task(
                hass.config_entries.async_reload(entry.entry_id),
                f"config entry reload {entry.title} {entry.domain} {entry.entry_id}",
            )
            return

        if not event.device or not event.device.id_string:
            return

        event_data = {
            "packet_type": event.device.packettype,
            "sub_type": event.device.subtype,
            "type_string": event.device.type_string,
            "id_string": event.device.id_string,
            "data": binascii.hexlify(event.data).decode("ASCII"),
            "values": getattr(event, "values", None),
        }

        _LOGGER.debug("Receive RFXCOM event: %s", event_data)

        data_bits = get_device_data_bits(event.device, devices)
        device_id = get_device_id(event.device, data_bits=data_bits)

        if device_id not in devices:
            if config[CONF_AUTOMATIC_ADD]:
                _add_device(event, device_id)
            else:
                return

        if event.device.packettype == DEVICE_PACKET_TYPE_LIGHTING4:
            find_possible_pt2262_device(pt2262_devices, event.device.id_string)
            pt2262_devices.add(event.device.id_string)

        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, *device_id)},  # type: ignore[arg-type]
        )
        if device_entry:
            event_data[ATTR_DEVICE_ID] = device_entry.id

        # Callback to HA registered components.
        async_dispatcher_send(hass, SIGNAL_EVENT, event, device_id)

        # Signal event to any other listeners
        hass.bus.async_fire(EVENT_RFXTRX_EVENT, event_data)