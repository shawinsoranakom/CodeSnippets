async def test_subway_subentry_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_subway_feed: MagicMock,
) -> None:
    """Test the subway subentry flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "stop"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "127N"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1 - Times Sq - 42 St (N direction)"
    assert result["data"] == {
        CONF_LINE: "1",
        CONF_STOP_ID: "127N",
        CONF_STOP_NAME: "Times Sq - 42 St (N direction)",
    }