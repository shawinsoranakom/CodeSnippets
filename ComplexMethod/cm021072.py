async def test_reauth_fixed_via_dashboard_at_confirm(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_dashboard: dict[str, Any],
) -> None:
    """Test reauth fixed automatically via dashboard at confirm step."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6053,
            CONF_PASSWORD: "",
            CONF_DEVICE_NAME: "test",
        },
        unique_id="11:22:33:44:55:aa",
    )
    entry.add_to_hass(hass)

    mock_client.device_info.return_value = DeviceInfo(
        uses_password=False, name="test", mac_address="11:22:33:44:55:aa"
    )

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM, result
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"] == {
        "name": "Mock Title (test)",
    }

    mock_dashboard["configured"].append(
        {
            "name": "test",
            "configuration": "test.yaml",
        }
    )

    await dashboard.async_get_dashboard(hass).async_refresh()

    with patch(
        "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_encryption_key",
        return_value=VALID_NOISE_PSK,
    ) as mock_get_encryption_key:
        # We just fetch the form
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT, result
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_NOISE_PSK] == VALID_NOISE_PSK

    assert len(mock_get_encryption_key.mock_calls) == 1