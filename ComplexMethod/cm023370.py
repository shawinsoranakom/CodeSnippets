async def test_creating_route(
    hass: HomeAssistant,
    mock_nsapi: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test creating a route after setting up the main config entry."""
    mock_config_entry.add_to_hass(hass)
    assert len(mock_config_entry.subentries) == 2
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "route"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_FROM: "ASD",
            CONF_TO: "RTD",
            CONF_VIA: "HT",
            CONF_NAME: "Home to Work",
            CONF_TIME: "08:30",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home to Work"
    assert result["data"] == {
        CONF_FROM: "ASD",
        CONF_TO: "RTD",
        CONF_VIA: "HT",
        CONF_NAME: "Home to Work",
        CONF_TIME: "08:30",
    }
    assert len(mock_config_entry.subentries) == 3