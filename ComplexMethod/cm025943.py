async def service_event_register_modify(call: ServiceCall) -> None:
    """Service for adding or removing a GroupAddress to the knx_event filter."""
    knx_module = get_knx_module(call.hass)

    attr_address = call.data[KNX_ADDRESS]
    group_addresses = list(map(parse_device_group_address, attr_address))

    if call.data.get(SERVICE_KNX_ATTR_REMOVE):
        for group_address in group_addresses:
            try:
                knx_module.knx_event_callback.group_addresses.remove(group_address)
            except ValueError:
                _LOGGER.warning(
                    "Service event_register could not remove event for '%s'",
                    str(group_address),
                )
            if group_address in knx_module.group_address_transcoder:
                del knx_module.group_address_transcoder[group_address]
        return

    if (dpt := call.data.get(CONF_TYPE)) and (
        transcoder := DPTBase.parse_transcoder(dpt)
    ):
        knx_module.group_address_transcoder.update(
            dict.fromkeys(group_addresses, transcoder)
        )
    for group_address in group_addresses:
        if group_address in knx_module.knx_event_callback.group_addresses:
            continue
        knx_module.knx_event_callback.group_addresses.append(group_address)
        _LOGGER.debug(
            "Service event_register registered event for '%s'",
            str(group_address),
        )