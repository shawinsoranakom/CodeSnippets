async def test_user_connection_works(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PORT: 80},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 80,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
        CONF_DEVICE_NAME: "test",
    }
    assert result["options"] == {
        CONF_ALLOW_SERVICE_CALLS: DEFAULT_NEW_CONFIG_ALLOW_ALLOW_SERVICE_CALLS
    }
    assert result["title"] == "test"
    assert result["result"].unique_id == "11:22:33:44:55:aa"

    assert len(mock_client.connect.mock_calls) == 1
    assert len(mock_client.device_info.mock_calls) == 1
    assert len(mock_client.disconnect.mock_calls) == 1
    assert mock_client.host == "127.0.0.1"
    assert mock_client.port == 80
    assert mock_client.password == ""
    assert mock_client.noise_psk is None