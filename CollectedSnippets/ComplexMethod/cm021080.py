async def test_reconfig_success_noise_psk_changes(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test reconfig initiation with new ip and new noise psk."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6053,
            CONF_PASSWORD: "",
            CONF_DEVICE_NAME: "test",
            CONF_NOISE_PSK: VALID_NOISE_PSK,
        },
        unique_id="11:22:33:44:55:aa",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    mock_client.device_info.side_effect = [
        RequiresEncryptionAPIError,
        InvalidEncryptionKeyAPIError("Wrong key", "test"),
        DeviceInfo(uses_password=False, name="test", mac_address="11:22:33:44:55:aa"),
    ]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.1", CONF_PORT: 6053}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encryption_key"
    assert result["description_placeholders"] == {"name": "Mock Title (test)"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: VALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encryption_key"
    assert result["description_placeholders"] == {"name": "Mock Title (test)"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: VALID_NOISE_PSK}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "127.0.0.1"
    assert entry.data[CONF_DEVICE_NAME] == "test"
    assert entry.data[CONF_NOISE_PSK] == VALID_NOISE_PSK