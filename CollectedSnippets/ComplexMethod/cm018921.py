async def test_reconfigure_duplicate(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_setup_entry: AsyncMock
) -> None:
    """Test reconfigure duplicate flow."""
    other_config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "2.3.4.5",
            CONF_PORT: 2345,
        },
        entry_id="other",
    )
    other_config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert not result["errors"]

    # Duplicate server
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    assert len(mock_setup_entry.mock_calls) == 0
    assert config_entry.data == {CONF_HOST: "1.2.3.4", CONF_PORT: 1234}
    assert other_config_entry.data == {CONF_HOST: "2.3.4.5", CONF_PORT: 2345}