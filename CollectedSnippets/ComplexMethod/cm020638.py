async def test_async_step_user_short_payload_then_full(hass: HomeAssistant) -> None:
    """Test setup from service info cache with devices found."""
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

    async def _async_process_advertisements(
        _hass, _callback, _matcher, _mode, _timeout
    ):
        service_info = make_advertisement(
            "A4:C1:38:56:53:84",
            b"XX\xe4\x16,\x84SV8\xc1\xa4+n\xf2\xe9\x12\x00\x00l\x88M\x9e",
        )
        assert _callback(service_info)
        return service_info

    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.async_process_advertisements",
        _async_process_advertisements,
    ):
        result1 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "A4:C1:38:56:53:84"},
        )
    assert result1["type"] is FlowResultType.MENU
    assert result1["step_id"] == "get_encryption_key_4_5_choose_method"

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        user_input={"next_step_id": "get_encryption_key_4_5"},
    )

    with patch(
        "homeassistant.components.xiaomi_ble.async_setup_entry", return_value=True
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={"bindkey": "a115210eed7a88e50ad52662e732a9fb"},
        )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Temperature/Humidity Sensor 5384 (LYWSD03MMC)"
    assert result3["data"] == {"bindkey": "a115210eed7a88e50ad52662e732a9fb"}