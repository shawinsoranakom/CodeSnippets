async def _async_port_entities_list(
    avm_wrapper: AvmWrapper, device_friendly_name: str, local_ip: str
) -> list[FritzBoxPortSwitch]:
    """Get list of port forwarding entities."""

    _LOGGER.debug("Setting up %s switches", SWITCH_TYPE_PORTFORWARD)
    entities_list: list[FritzBoxPortSwitch] = []
    if not avm_wrapper.device_conn_type:
        _LOGGER.debug("The FRITZ!Box has no %s options", SWITCH_TYPE_PORTFORWARD)
        return []

    # Query port forwardings and setup a switch for each forward for the current device
    resp = await avm_wrapper.async_get_num_port_mapping(avm_wrapper.device_conn_type)
    if not resp:
        _LOGGER.debug("The FRITZ!Box has no %s options", SWITCH_TYPE_PORTFORWARD)
        return []

    port_forwards_count: int = resp["NewPortMappingNumberOfEntries"]

    _LOGGER.debug(
        "Specific %s response: GetPortMappingNumberOfEntries=%s",
        SWITCH_TYPE_PORTFORWARD,
        port_forwards_count,
    )

    _LOGGER.debug("IP source for %s is %s", avm_wrapper.host, local_ip)

    for i in range(port_forwards_count):
        portmap = await avm_wrapper.async_get_port_mapping(
            avm_wrapper.device_conn_type, i
        )
        if not portmap:
            _LOGGER.debug("The FRITZ!Box has no %s options", SWITCH_TYPE_DEFLECTION)
            continue

        _LOGGER.debug(
            "Specific %s response: GetGenericPortMappingEntry=%s",
            SWITCH_TYPE_PORTFORWARD,
            portmap,
        )

        # We can only handle port forwards of the given device
        if portmap["NewInternalClient"] == local_ip:
            port_name = portmap["NewPortMappingDescription"]
            for entity in entities_list:
                if entity.port_mapping and (
                    port_name in entity.port_mapping["NewPortMappingDescription"]
                ):
                    port_name = f"{port_name} {portmap['NewExternalPort']}"
            entities_list.append(
                FritzBoxPortSwitch(
                    avm_wrapper,
                    device_friendly_name,
                    portmap,
                    port_name,
                    i,
                    avm_wrapper.device_conn_type,
                )
            )

    return entities_list