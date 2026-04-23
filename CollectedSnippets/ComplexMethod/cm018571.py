async def test_options_flow_ble(hass: HomeAssistant, mock_rpc_device: Mock) -> None:
    """Test setting ble options for gen2 devices."""
    entry = await init_integration(hass, 2)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BLE_SCANNER_MODE: BLEScannerMode.DISABLED,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BLE_SCANNER_MODE] is BLEScannerMode.DISABLED

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BLE_SCANNER_MODE] is BLEScannerMode.ACTIVE

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BLE_SCANNER_MODE: BLEScannerMode.PASSIVE,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BLE_SCANNER_MODE] is BLEScannerMode.PASSIVE

    await hass.config_entries.async_unload(entry.entry_id)