async def test_user_step_unknown_exception(hass: HomeAssistant) -> None:
    """Test user step with an unknown exception."""
    with patch(
        "homeassistant.components.ld2410_ble.config_flow.async_discovered_service_info",
        return_value=[NOT_LD2410_BLE_DISCOVERY_INFO, LD2410_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.ld2410_ble.config_flow.LD2410BLE.initialise",
        side_effect=RuntimeError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: LD2410_BLE_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "unknown"}

    with (
        patch(
            "homeassistant.components.ld2410_ble.config_flow.LD2410BLE.initialise",
        ),
        patch(
            "homeassistant.components.ld2410_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_ADDRESS: LD2410_BLE_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == LD2410_BLE_DISCOVERY_INFO.name
    assert result3["data"] == {
        CONF_ADDRESS: LD2410_BLE_DISCOVERY_INFO.address,
    }
    assert result3["result"].unique_id == LD2410_BLE_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1