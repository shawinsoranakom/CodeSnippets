async def test_reauth_fails(
    hass: HomeAssistant, error: Exception, message: str, mock_api: MagicMock
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    mock_api.return_value.get_ha_sensor_data.side_effect = [error, HA_SENSOR_DATA]
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: "Mock Title",
        CONF_USERNAME: "username",
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": message}

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"