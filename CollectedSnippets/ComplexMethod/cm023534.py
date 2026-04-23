async def test_user_setup_wohand_replaces_ignored(hass: HomeAssistant) -> None:
    """Test setting up a switchbot replaces an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, unique_id="aabbccddeeff", source=SOURCE_IGNORE
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[WOHAND_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bot EEFF"
    assert result["data"] == {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_SENSOR_TYPE: "bot",
    }

    assert len(mock_setup_entry.mock_calls) == 1