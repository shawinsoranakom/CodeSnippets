async def test_user_flow_with_credentials(
    hass: HomeAssistant, mock_nrgkick_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we can setup when authentication is required."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_nrgkick_api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "NRGkick Test"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "test_user",
        CONF_PASSWORD: "test_pass",
    }
    assert result["result"].unique_id == "TEST123456"
    mock_setup_entry.assert_called_once()