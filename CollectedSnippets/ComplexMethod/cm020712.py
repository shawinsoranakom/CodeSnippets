async def test_migration_resets_old_radio(
    hass: HomeAssistant, backup, mock_app
) -> None:
    """Test that the old radio is reset during migration."""
    entry = MockConfigEntry(
        version=config_flow.ZhaConfigFlowHandler.VERSION,
        domain=DOMAIN,
        data={
            CONF_DEVICE: {
                CONF_DEVICE_PATH: "/dev/ttyUSB0",
                CONF_BAUDRATE: 115200,
                CONF_FLOW_CONTROL: None,
            },
            CONF_RADIO_TYPE: "ezsp",
        },
    )
    entry.add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )

    mock_temp_radio_mgr = AsyncMock()
    mock_temp_radio_mgr.async_reset_adapter = AsyncMock()

    with (
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager._async_read_backups_from_database",
            return_value=[backup],
        ),
        patch(
            "homeassistant.components.zha.config_flow.ZhaRadioManager",
            side_effect=[ZhaRadioManager(), mock_temp_radio_mgr],
        ),
    ):
        result_init = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
        )

        result_confirm = await hass.config_entries.flow.async_configure(
            result_init["flow_id"], user_input={}
        )

        assert result_confirm["step_id"] == "choose_migration_strategy"

        result_migrate = await hass.config_entries.flow.async_configure(
            result_confirm["flow_id"],
            user_input={"next_step_id": config_flow.MIGRATION_STRATEGY_RECOMMENDED},
        )

        result_recommended = await consume_progress_flow(
            hass,
            flow_id=result_migrate["flow_id"],
            valid_step_ids=("maybe_reset_old_radio", "restore_backup"),
        )

    assert result_recommended["type"] is FlowResultType.ABORT
    assert result_recommended["reason"] == "reconfigure_successful"

    # We reset the old radio
    assert mock_temp_radio_mgr.async_reset_adapter.call_count == 1

    # It should be configured with the old radio's settings
    assert mock_temp_radio_mgr.radio_type == RadioType.ezsp
    assert mock_temp_radio_mgr.device_path == "/dev/ttyUSB0"
    assert mock_temp_radio_mgr.device_settings == {
        CONF_DEVICE_PATH: "/dev/ttyUSB0",
        CONF_BAUDRATE: 115200,
        CONF_FLOW_CONTROL: None,
    }