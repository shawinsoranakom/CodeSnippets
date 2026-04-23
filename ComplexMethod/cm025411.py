async def websocket_create_network(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
    data: OTBRData,
) -> None:
    """Create a new Thread network."""
    channel = await get_allowed_channel(hass, data.url) or DEFAULT_CHANNEL

    try:
        await data.set_enabled(False)
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "set_enabled_failed", str(exc))
        return

    try:
        await data.factory_reset(hass)
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "factory_reset_failed", str(exc))
        return

    pan_id = generate_random_pan_id()
    try:
        await data.create_active_dataset(
            python_otbr_api.ActiveDataSet(
                channel=channel,
                network_name=compose_default_network_name(pan_id),
                pan_id=pan_id,
            )
        )
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "create_active_dataset_failed", str(exc))
        return

    try:
        await data.set_enabled(True)
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "set_enabled_failed", str(exc))
        return

    try:
        dataset_tlvs = await data.get_active_dataset_tlvs()
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "get_active_dataset_tlvs_failed", str(exc))
        return
    if not dataset_tlvs:
        connection.send_error(msg["id"], "get_active_dataset_tlvs_empty", "")
        return

    await async_add_dataset(hass, DOMAIN, dataset_tlvs.hex())

    # Update repair issues
    await update_issues(hass, data, dataset_tlvs)

    connection.send_result(msg["id"])