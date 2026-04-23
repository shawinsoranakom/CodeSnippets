async def test_hardware_migration_flow_strategy_advanced(
    hass: HomeAssistant,
    backup: zigpy.backups.NetworkBackup,
    mock_app: AsyncMock,
) -> None:
    """Test advanced flow strategy for hardware migration flow."""
    entry = MockConfigEntry(
        version=config_flow.ZhaConfigFlowHandler.VERSION,
        domain=DOMAIN,
        data={
            CONF_DEVICE: {
                CONF_DEVICE_PATH: "/dev/ttyUSB0",
                CONF_BAUDRATE: 115200,
                CONF_FLOW_CONTROL: None,
            },
            CONF_RADIO_TYPE: "znp",
        },
    )
    entry.add_to_hass(hass)

    data = {
        "name": "Yellow",
        "radio_type": "efr32",
        "port": {
            "path": "/dev/ttyAMA1",
            "baudrate": 115200,
            "flow_control": "hardware",
        },
        "flow_strategy": "advanced",
    }
    with (
        patch(
            "homeassistant.components.onboarding.async_is_onboarded", return_value=True
        ),
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager._async_read_backups_from_database",
            return_value=[backup],
        ),
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager.restore_backup",
        ) as mock_restore_backup,
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload",
            return_value=True,
        ) as mock_async_unload,
    ):
        result_hardware = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_HARDWARE}, data=data
        )

        assert result_hardware["type"] is FlowResultType.FORM
        assert result_hardware["step_id"] == "confirm"

        result_confirm = await hass.config_entries.flow.async_configure(
            result_hardware["flow_id"], user_input={}
        )

        assert result_confirm["type"] is FlowResultType.MENU
        assert result_confirm["step_id"] == "choose_formation_strategy"

        result_form = await hass.config_entries.flow.async_configure(
            result_confirm["flow_id"],
            user_input={"next_step_id": "form_new_network"},
        )

        result_formation_strategy = await consume_progress_flow(
            hass,
            flow_id=result_form["flow_id"],
            valid_step_ids=("form_new_network",),
        )
        await hass.async_block_till_done()

    assert result_formation_strategy["type"] is FlowResultType.ABORT
    assert result_formation_strategy["reason"] == "reconfigure_successful"
    assert mock_async_unload.call_count == 0
    assert mock_restore_backup.call_count == 0