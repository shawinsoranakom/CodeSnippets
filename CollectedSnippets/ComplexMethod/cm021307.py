async def test_login_errors(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_client: AsyncMock
) -> None:
    """Test login errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.totalconnect.config_flow.TotalConnectClient",
    ) as client:
        client.side_effect = AuthenticationError()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "locations"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY