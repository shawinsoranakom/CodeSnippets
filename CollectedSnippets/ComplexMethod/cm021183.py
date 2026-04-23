async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_tailwind: MagicMock,
    side_effect: Exception,
    expected_error: dict[str, str],
) -> None:
    """Test the reconfiguration flow recovers from errors."""
    mock_config_entry.add_to_hass(hass)
    mock_tailwind.status.side_effect = side_effect

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == expected_error

    mock_tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"