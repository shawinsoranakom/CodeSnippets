async def test_reconfigure_flow(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_setup_entry: AsyncMock
) -> None:
    """Test reconfigure flow."""
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert not result["errors"]

    # Invalid server
    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}

    # Valid server
    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == {CONF_HOST: "2.3.4.5", CONF_PORT: 2345}

    assert len(mock_setup_entry.mock_calls) == 1