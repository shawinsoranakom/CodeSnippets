async def test_user_show_menu_when_passive_scanner_present(hass: HomeAssistant) -> None:
    """Test that menu is shown when any scanner is in passive mode."""
    mock_scanner_active = Mock()
    mock_scanner_active.current_mode = BluetoothScanningMode.ACTIVE
    mock_scanner_passive = Mock()
    mock_scanner_passive.current_mode = BluetoothScanningMode.PASSIVE

    with (
        patch(
            "homeassistant.components.bluetooth.async_current_scanners",
            return_value=[mock_scanner_active, mock_scanner_passive],
        ),
        patch(
            "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
            return_value=[WOHAND_SERVICE_INFO],
        ),
        patch_async_setup_entry() as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        # Should show menu since not all scanners are active
        assert result["type"] is FlowResultType.MENU
        assert result["step_id"] == "user"
        assert set(result["menu_options"]) == {"cloud_login", "select_device"}

        # Choose select_device from menu
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "select_device"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "confirm"

        # Confirm the device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bot EEFF"
    assert result["data"] == {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_SENSOR_TYPE: "bot",
    }
    assert len(mock_setup_entry.mock_calls) == 1