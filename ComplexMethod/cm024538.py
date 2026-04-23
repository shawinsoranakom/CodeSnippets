async def test_bus_subentry_flow(
    hass: HomeAssistant,
    mock_config_entry_with_api_key: MockConfigEntry,
    mock_bus_feed: MagicMock,
) -> None:
    """Test the bus subentry flow."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "stop"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "M15 - 1 Av/E 79 St"
    assert result["data"] == {
        CONF_ROUTE: "M15",
        CONF_STOP_ID: "400561",
        CONF_STOP_NAME: "1 Av/E 79 St",
    }