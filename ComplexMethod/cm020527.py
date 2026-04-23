async def test_reconfigure_auth_discovered(
    hass: HomeAssistant,
    mock_added_config_entry: MockConfigEntry,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test reconfigure auth flow for device that's discovered."""
    result = await mock_added_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Simulate a bad host
    with (
        override_side_effect(
            mock_discovery["mock_devices"][IP_ADDRESS].update, KasaException
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "WRONG_IP",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}
    assert "error" in result["description_placeholders"]

    with (
        override_side_effect(
            mock_discovery["mock_devices"][IP_ADDRESS].update, AuthenticationError
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: IP_ADDRESS,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"