async def test_step_reauth(
    hass: HomeAssistant,
    mqtt_client_mock: MqttMockPahoClient,
    mock_try_connection: MagicMock,
    test_input: dict[str, Any],
    user_input: dict[str, Any],
    new_password: str,
) -> None:
    """Test that the reauth step works."""

    # Prepare the config entry
    config_entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data=test_input,
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)

    # Start reauth flow
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"
    assert result["context"]["source"] == "reauth"

    # Show the form
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Simulate re-auth fails
    mock_try_connection.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Simulate re-auth succeeds
    mock_try_connection.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert len(hass.config_entries.async_entries()) == 1
    assert config_entry.data.get(CONF_PASSWORD) == new_password
    await hass.async_block_till_done()