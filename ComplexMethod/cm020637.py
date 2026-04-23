async def test_async_step_user_short_payload(hass: HomeAssistant) -> None:
    """Test setup from service info cache with devices found but short payloads."""
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.async_discovered_service_info",
        return_value=[MISSING_PAYLOAD_ENCRYPTED],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.async_process_advertisements",
        side_effect=TimeoutError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "A4:C1:38:56:53:84"},
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "confirm_slow"

    with patch(
        "homeassistant.components.xiaomi_ble.async_setup_entry", return_value=True
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Temperature/Humidity Sensor 5384 (LYWSD03MMC)"
    assert result3["data"] == {}
    assert result3["result"].unique_id == "A4:C1:38:56:53:84"