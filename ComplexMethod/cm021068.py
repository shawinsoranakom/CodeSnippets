async def test_login_connection_error(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test user step with connection error on login attempt."""
    mock_client.device_info.return_value = DeviceInfo(uses_password=True, name="test")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authenticate"
    assert result["description_placeholders"] == {"name": "test"}

    mock_client.connect.side_effect = APIConnectionError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "valid"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authenticate"
    assert result["description_placeholders"] == {"name": "test"}
    assert result["errors"] == {"base": "connection_error"}

    mock_client.connect.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "good"}
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "test"
    assert result2["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 6053,
        CONF_DEVICE_NAME: "test",
        CONF_PASSWORD: "good",
        CONF_NOISE_PSK: "",
    }