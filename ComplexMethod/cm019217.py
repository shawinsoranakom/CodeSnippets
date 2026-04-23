async def test_bluetooth_step_cannot_connect(hass: HomeAssistant, exc, error) -> None:
    """Test bluetooth step and we cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "associate"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == error