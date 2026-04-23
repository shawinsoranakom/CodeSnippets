async def test_user_flow_self_hosted_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_authenticator_authenticate: AsyncMock,
    mock_mqtt_client: Mock,
) -> None:
    """Test handling selfhosted errors and custom ssl context."""

    result = await _test_user_flow_show_advanced_options(
        hass,
        _TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED
            | {
                CONF_OVERRIDE_REST_URL: "bla://localhost:8000",
                CONF_OVERRIDE_MQTT_URL: "mqtt://",
            },
            _USER_STEP_SELF_HOSTED,
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {
        CONF_OVERRIDE_REST_URL: "invalid_url_schema_override_rest_url",
        CONF_OVERRIDE_MQTT_URL: "invalid_url",
    }
    mock_authenticator_authenticate.assert_not_called()
    mock_mqtt_client.verify_config.assert_not_called()
    mock_setup_entry.assert_not_called()

    # Check that the schema includes select box to disable ssl verification of mqtt
    assert CONF_VERIFY_MQTT_CERTIFICATE in result["data_schema"].schema

    data = VALID_ENTRY_DATA_SELF_HOSTED | {CONF_VERIFY_MQTT_CERTIFICATE: False}
    with patch(
        "homeassistant.components.ecovacs.config_flow.create_mqtt_config",
        wraps=create_mqtt_config,
    ) as mock_create_mqtt_config:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=data,
        )
        mock_create_mqtt_config.assert_called_once()
        ssl_context = mock_create_mqtt_config.call_args[1]["ssl_context"]
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == data[CONF_USERNAME]
    assert result["data"] == data
    mock_setup_entry.assert_called()
    mock_authenticator_authenticate.assert_called()
    mock_mqtt_client.verify_config.assert_called()