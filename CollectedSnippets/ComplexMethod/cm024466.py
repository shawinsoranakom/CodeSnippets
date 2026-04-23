async def test_subentry_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    """Test creating a location subentry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # After initial setup for 1 subentry, each API is called once
    assert mock_api.async_get_current_conditions.call_count == 1

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "location"),
        context={"source": "user"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Work",
            CONF_LOCATION: {
                CONF_LATITUDE: 30.1,
                CONF_LONGITUDE: 40.1,
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Work"
    assert result["data"] == {
        CONF_LATITUDE: 30.1,
        CONF_LONGITUDE: 40.1,
    }

    # Initial setup: 1 of each API call
    # Subentry flow validation: 1 current conditions call
    # Reload with 2 subentries: 2 of each API call
    assert mock_api.async_get_current_conditions.call_count == 1 + 1 + 2

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert len(entry.subentries) == 2