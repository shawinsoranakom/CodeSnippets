async def websocket_info(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Get OTBR info."""
    config_entries: list[OTBRConfigEntry]
    config_entries = hass.config_entries.async_loaded_entries(DOMAIN)

    if not config_entries:
        connection.send_error(msg["id"], "not_loaded", "No OTBR API loaded")
        return

    response: dict[str, dict[str, Any]] = {}

    for config_entry in config_entries:
        data = config_entry.runtime_data
        try:
            border_agent_id = await data.get_border_agent_id()
            dataset = await data.get_active_dataset()
            dataset_tlvs = await data.get_active_dataset_tlvs()
            extended_address = (await data.get_extended_address()).hex()
        except HomeAssistantError as exc:
            connection.send_error(msg["id"], "otbr_info_failed", str(exc))
            return

        # The border agent ID is checked when the OTBR config entry is setup,
        # we can assert it's not None
        assert border_agent_id is not None

        extended_pan_id = (
            dataset.extended_pan_id.lower()
            if dataset and dataset.extended_pan_id
            else None
        )
        response[extended_address] = {
            "active_dataset_tlvs": dataset_tlvs.hex() if dataset_tlvs else None,
            "border_agent_id": border_agent_id.hex(),
            "channel": dataset.channel if dataset else None,
            "extended_address": extended_address,
            "extended_pan_id": extended_pan_id,
            "url": data.url,
        }

    connection.send_result(msg["id"], response)