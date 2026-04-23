async def test_reauth_confirm_invalid_with_unique_id(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test reauth initiation with invalid PSK."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 6053, CONF_PASSWORD: ""},
        unique_id="11:22:33:44:55:aa",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    mock_client.device_info.side_effect = InvalidEncryptionKeyAPIError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: INVALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"] == {
        "name": "Mock Title (test)",
    }
    assert result["errors"]
    assert result["errors"]["base"] == "invalid_psk"

    device_info = DeviceInfo(
        uses_password=False, name="test", mac_address="11:22:33:44:55:aa"
    )
    mock_client.device_info = AsyncMock(return_value=device_info)
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device_info, [], [])
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: VALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_NOISE_PSK] == VALID_NOISE_PSK