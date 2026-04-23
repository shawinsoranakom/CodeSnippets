async def websocket_set_network(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
    data: OTBRData,
) -> None:
    """Set the Thread network to be used by the OTBR."""
    dataset_tlv = await async_get_dataset(hass, msg["dataset_id"])

    if not dataset_tlv:
        connection.send_error(msg["id"], "unknown_dataset", "Unknown dataset")
        return
    dataset = tlv_parser.parse_tlv(dataset_tlv)
    if channel := dataset.get(MeshcopTLVType.CHANNEL):
        thread_dataset_channel = cast(tlv_parser.Channel, channel).channel

    allowed_channel = await get_allowed_channel(hass, data.url)

    if allowed_channel and thread_dataset_channel != allowed_channel:
        connection.send_error(
            msg["id"],
            "channel_conflict",
            f"Can't connect to network on channel {thread_dataset_channel}, ZHA is "
            f"using channel {allowed_channel}",
        )
        return

    try:
        await data.set_enabled(False)
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "set_enabled_failed", str(exc))
        return

    try:
        await data.set_active_dataset_tlvs(bytes.fromhex(dataset_tlv))
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "set_active_dataset_tlvs_failed", str(exc))
        return

    try:
        await data.set_enabled(True)
    except HomeAssistantError as exc:
        connection.send_error(msg["id"], "set_enabled_failed", str(exc))
        return

    # Update repair issues
    await update_issues(hass, data, bytes.fromhex(dataset_tlv))

    connection.send_result(msg["id"])