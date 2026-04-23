async def websocket_unprovision_smart_start_node(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
    entry: ZwaveJSConfigEntry,
    client: Client,
    driver: Driver,
) -> None:
    """Unprovision a smart start node."""
    try:
        cv.has_at_least_one_key(DSK, NODE_ID)(msg)
    except vol.Invalid as err:
        connection.send_error(
            msg[ID],
            ERR_INVALID_FORMAT,
            err.args[0],
        )
        return
    dsk_or_node_id = msg.get(DSK) or msg[NODE_ID]
    provisioning_entry = await driver.controller.async_get_provisioning_entry(
        dsk_or_node_id
    )
    if (
        provisioning_entry
        and provisioning_entry.additional_properties
        and "device_id" in provisioning_entry.additional_properties
    ):
        device_identifier = (DOMAIN, f"provision_{provisioning_entry.dsk}")
        device_id = provisioning_entry.additional_properties["device_id"]
        dev_reg = dr.async_get(hass)
        device = dev_reg.async_get(device_id)
        if device and device.identifiers == {device_identifier}:
            # Only remove the device if nothing else has claimed it
            dev_reg.async_remove_device(device_id)

    await driver.controller.async_unprovision_smart_start_node(dsk_or_node_id)

    connection.send_result(msg[ID])