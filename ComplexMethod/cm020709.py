async def test_options_flow_migration_reset_old_adapter(
    hass: HomeAssistant, backup, mock_app
) -> None:
    """Test options flow for migrating resets the old radio, not the new one."""

    entry = MockConfigEntry(
        version=config_flow.ZhaConfigFlowHandler.VERSION,
        domain=DOMAIN,
        data={
            CONF_DEVICE: {
                CONF_DEVICE_PATH: "/dev/ttyUSB_old",
                CONF_BAUDRATE: 12345,
                CONF_FLOW_CONTROL: None,
            },
            CONF_RADIO_TYPE: "znp",
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(entry.entry_id)

    # ZHA gets unloaded
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload", return_value=True
    ):
        result_init = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input={}
        )

    entry.mock_state(hass, ConfigEntryState.NOT_LOADED)

    assert result_init["step_id"] == "prompt_migrate_or_reconfigure"

    with (
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager.detect_radio_type",
            return_value=ProbeResult.RADIO_TYPE_DETECTED,
        ),
        patch(
            "homeassistant.components.zha.config_flow.list_serial_ports",
            AsyncMock(return_value=[usb_port("/dev/ttyUSB_new")]),
        ),
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager._async_read_backups_from_database",
            return_value=[backup],
        ),
    ):
        result_migrate = await hass.config_entries.options.async_configure(
            flow["flow_id"],
            user_input={"next_step_id": config_flow.OptionsMigrationIntent.MIGRATE},
        )

        # Now we choose the new radio
        assert result_migrate["step_id"] == "choose_serial_port"

        result_port = await hass.config_entries.options.async_configure(
            flow["flow_id"],
            user_input={
                CONF_DEVICE_PATH: "/dev/ttyUSB_new - Some serial port, s/n: 1234 - Virtual serial port"
            },
        )

    assert result_port["step_id"] == "choose_migration_strategy"

    # A temporary radio manager is created to reset the old adapter
    mock_radio_manager = AsyncMock()

    with patch(
        "homeassistant.components.zha.config_flow.ZhaRadioManager",
        spec=ZhaRadioManager,
        side_effect=[mock_radio_manager],
    ):
        result_migrate_start = await hass.config_entries.options.async_configure(
            flow["flow_id"],
            user_input={
                "next_step_id": config_flow.MIGRATION_STRATEGY_RECOMMENDED,
            },
        )

        result_strategy = await consume_progress_flow(
            hass,
            flow_id=result_migrate_start["flow_id"],
            valid_step_ids=("maybe_reset_old_radio", "restore_backup"),
            flow_manager=hass.config_entries.options,
        )

    # The old adapter is reset, not the new one
    assert mock_radio_manager.device_path == "/dev/ttyUSB_old"
    assert mock_radio_manager.async_reset_adapter.call_count == 1

    assert result_strategy["type"] is FlowResultType.ABORT
    assert result_strategy["reason"] == "reconfigure_successful"

    # The entry is updated
    assert entry.data["device"]["path"] == "/dev/ttyUSB_new"