async def test_need_authorization_fails(hass: HomeAssistant, exc, error) -> None:
    """Test bluetooth flow with error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=IMPROV_BLE_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] is None

    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.can_identify",
            return_value=False,
            new_callable=PropertyMock,
        ),
        patch(f"{IMPROV_BLE}.config_flow.ImprovBLEClient.ensure_connected"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: IMPROV_BLE_DISCOVERY_INFO.address},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provision"

    with patch(
        f"{IMPROV_BLE}.config_flow.ImprovBLEClient.need_authorization", side_effect=exc
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"ssid": "MyWIFI", "password": "secret"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == error