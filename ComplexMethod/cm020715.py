async def test_plug_in_old_radio_retry(hass: HomeAssistant, backup, mock_app) -> None:
    """Test plug_in_old_radio step when reset fails due to unplugged adapter."""
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
    mock_temp_radio_mgr.async_reset_adapter = DelayedAsyncMock(
        side_effect=HomeAssistantError(
            "Failed to connect to Zigbee adapter: [Errno 2] No such file or directory"
        )
    )

    with (
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager._async_read_backups_from_database",
            return_value=[backup],
        ),
        patch(
            "homeassistant.components.zha.config_flow.ZhaRadioManager",
            side_effect=[ZhaRadioManager(), mock_temp_radio_mgr, mock_temp_radio_mgr],
        ),
    ):
        result_init = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
        )

        result_confirm = await hass.config_entries.flow.async_configure(
            result_init["flow_id"], user_input={}
        )

        assert result_confirm["step_id"] == "choose_migration_strategy"

        recommended_result = await hass.config_entries.flow.async_configure(
            result_confirm["flow_id"],
            user_input={"next_step_id": config_flow.MIGRATION_STRATEGY_RECOMMENDED},
        )

        result_recommended = await consume_progress_flow(
            hass,
            flow_id=recommended_result["flow_id"],
            valid_step_ids=("maybe_reset_old_radio",),
        )

        # Prompt user to plug old adapter back in when reset fails
        assert result_recommended["type"] is FlowResultType.MENU
        assert result_recommended["step_id"] == "plug_in_old_radio"
        assert (
            result_recommended["description_placeholders"]["device_path"]
            == "/dev/ttyUSB0"
        )
        assert result_recommended["menu_options"] == [
            "retry_old_radio",
            "skip_reset_old_radio",
        ]

        # Retry with unplugged adapter
        retry_result = await hass.config_entries.flow.async_configure(
            result_recommended["flow_id"],
            user_input={"next_step_id": "retry_old_radio"},
        )

        result_retry = await consume_progress_flow(
            hass,
            flow_id=retry_result["flow_id"],
            valid_step_ids=("maybe_reset_old_radio",),
        )

    # Prompt user again to plug old adapter back in
    assert result_retry["type"] is FlowResultType.MENU
    assert result_retry["step_id"] == "plug_in_old_radio"

    # Skip resetting the old adapter
    result_skip_progress = await hass.config_entries.flow.async_configure(
        result_retry["flow_id"],
        user_input={"next_step_id": "skip_reset_old_radio"},
    )

    result_skip = await consume_progress_flow(
        hass,
        flow_id=result_skip_progress["flow_id"],
        valid_step_ids=("maybe_reset_old_radio", "restore_backup"),
    )

    # Entry created successfully after skipping reset
    assert result_skip["type"] is FlowResultType.ABORT
    assert result_skip["reason"] == "reconfigure_successful"

    # Verify reset was attempted twice: initial + retry
    assert mock_temp_radio_mgr.async_reset_adapter.call_count == 2