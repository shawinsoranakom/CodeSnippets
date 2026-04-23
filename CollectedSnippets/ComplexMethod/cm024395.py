async def test_user_step_cannot_connect(hass: HomeAssistant) -> None:
    """Test user step and we cannot connect."""
    with patch(
        "homeassistant.components.led_ble.config_flow.async_discovered_service_info",
        return_value=[LED_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.led_ble.config_flow.LEDBLE.update",
        side_effect=BleakError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.led_ble.config_flow.LEDBLE.update",
        ),
        patch(
            "homeassistant.components.led_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == LED_BLE_DISCOVERY_INFO.name
    assert result3["data"] == {
        CONF_ADDRESS: LED_BLE_DISCOVERY_INFO.address,
    }
    assert result3["result"].unique_id == LED_BLE_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1