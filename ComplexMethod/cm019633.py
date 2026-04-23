async def test_options_flow_failures(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    opensky_client: AsyncMock,
    config_entry: MockConfigEntry,
    user_input: dict[str, Any],
    error: str,
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    opensky_client.authenticate.side_effect = OpenSkyUnauthenticatedError
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_RADIUS: 10000, **user_input},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"]["base"] == error
    opensky_client.authenticate.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RADIUS: 10000,
            CONF_USERNAME: "homeassistant",
            CONF_PASSWORD: "secret",
            CONF_CONTRIBUTING_USER: True,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_RADIUS: 10000,
        CONF_USERNAME: "homeassistant",
        CONF_PASSWORD: "secret",
        CONF_CONTRIBUTING_USER: True,
    }