async def test_user_resolve_error(hass: HomeAssistant, mock_client: APIClient) -> None:
    """Test user step with IP resolve error."""

    with patch(
        "homeassistant.components.esphome.config_flow.APIConnectionError",
        new_callable=lambda: ResolveAPIError,
    ) as exc:
        mock_client.device_info.side_effect = exc
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "resolve_error"}

    assert len(mock_client.connect.mock_calls) == 1
    assert len(mock_client.device_info.mock_calls) == 1
    assert len(mock_client.disconnect.mock_calls) == 1

    # Now simulate the user retrying with the same host and a successful connection
    mock_client.device_info.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "test"
    assert result2["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 6053,
        CONF_DEVICE_NAME: "test",
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
    }