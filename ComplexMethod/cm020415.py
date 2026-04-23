async def test_user_setup_unable_to_connect(hass: HomeAssistant) -> None:
    """Test the user initiated form with a device that's failing connection."""
    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert result["data_schema"] is not None
    schema = result["data_schema"].schema

    assert schema.get(CONF_ADDRESS).container == {
        "a0:d9:5a:57:0b:00": "InspectorBLE-D9A0"
    }

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(side_effect=BleakError("An error")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"