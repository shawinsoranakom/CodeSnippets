async def test_encryption_key_invalid_psk(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test encryption key step with invalid key."""

    mock_client.device_info.side_effect = RequiresEncryptionAPIError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encryption_key"
    assert result["description_placeholders"] == {"name": "ESPHome"}

    mock_client.device_info.side_effect = InvalidEncryptionKeyAPIError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: INVALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encryption_key"
    assert result["errors"] == {"base": "invalid_psk"}
    assert result["description_placeholders"] == {"name": "ESPHome"}
    assert mock_client.noise_psk == INVALID_NOISE_PSK

    mock_client.device_info.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_NOISE_PSK: VALID_NOISE_PSK}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: VALID_NOISE_PSK,
        CONF_DEVICE_NAME: "test",
    }
    assert mock_client.noise_psk == VALID_NOISE_PSK