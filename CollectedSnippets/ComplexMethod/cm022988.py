async def test_user_flow_raise_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_authenticator_authenticate: AsyncMock,
    mock_mqtt_client: Mock,
    side_effect_rest: Exception,
    reason_rest: str,
    side_effect_mqtt: Exception,
    errors_mqtt: Callable[[dict[str, Any]], str],
    test_fn: Callable[[HomeAssistant, _TestFnUserInput], Awaitable[dict[str, Any]]],
    test_fn_user_input: _TestFnUserInput,
    entry_data: dict[str, Any],
) -> None:
    """Test handling error on library calls."""
    user_input_auth = test_fn_user_input.auth

    # Authenticator raises error
    mock_authenticator_authenticate.side_effect = side_effect_rest
    result = await test_fn(hass, test_fn_user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": reason_rest}
    mock_authenticator_authenticate.assert_called()
    mock_mqtt_client.verify_config.assert_not_called()
    mock_setup_entry.assert_not_called()

    mock_authenticator_authenticate.reset_mock(side_effect=True)

    # MQTT raises error
    mock_mqtt_client.verify_config.side_effect = side_effect_mqtt
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input_auth,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == errors_mqtt(user_input_auth)
    mock_authenticator_authenticate.assert_called()
    mock_mqtt_client.verify_config.assert_called()
    mock_setup_entry.assert_not_called()

    mock_authenticator_authenticate.reset_mock(side_effect=True)
    mock_mqtt_client.verify_config.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input_auth,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == entry_data[CONF_USERNAME]
    assert result["data"] == entry_data
    mock_setup_entry.assert_called()
    mock_authenticator_authenticate.assert_called()
    mock_mqtt_client.verify_config.assert_called()