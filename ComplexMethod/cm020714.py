async def test_plug_in_new_radio_retry(
    allow_overwrite_ieee_mock,
    advanced_pick_radio: RadioPicker,
    mock_app: AsyncMock,
    backup,
    hass: HomeAssistant,
) -> None:
    """Test plug_in_new_radio step when restore fails due to unplugged adapter."""
    result = await advanced_pick_radio(RadioType.ezsp)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"next_step_id": config_flow.FORMATION_UPLOAD_MANUAL_BACKUP},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "upload_manual_backup"

    with (
        patch(
            "homeassistant.components.zha.config_flow.ZhaConfigFlowHandler._parse_uploaded_backup",
            return_value=backup,
        ),
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager.restore_backup",
            new_callable=DelayedAsyncMock,
            side_effect=[
                HomeAssistantError(
                    "Failed to connect to Zigbee adapter: [Errno 2] No such file or directory"
                ),
                DestructiveWriteNetworkSettings("Radio IEEE change is permanent"),
                HomeAssistantError(
                    "Failed to connect to Zigbee adapter: [Errno 2] No such file or directory"
                ),
                None,
            ],
        ) as mock_restore_backup,
    ):
        upload_result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={config_flow.UPLOADED_BACKUP_FILE: str(uuid.uuid4())},
        )

        result3 = await consume_progress_flow(
            hass,
            flow_id=upload_result["flow_id"],
            valid_step_ids=("restore_backup",),
        )

        # Prompt user to plug new adapter back in when restore fails
        assert result3["type"] is FlowResultType.FORM
        assert result3["step_id"] == "plug_in_new_radio"
        assert result3["description_placeholders"] == {"device_path": "/dev/ttyUSB1234"}

        # Submit retry attempt with plugged in adapter
        retry_result = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            user_input={},
        )

        result4 = await consume_progress_flow(
            hass,
            flow_id=retry_result["flow_id"],
            valid_step_ids=("restore_backup",),
        )

        # This adapter requires user confirmation for restore
        assert result4["type"] is FlowResultType.FORM
        assert result4["step_id"] == "confirm_ezsp_ieee_overwrite"

        # Confirm destructive rewrite, but adapter is unplugged again
        confirm_result = await hass.config_entries.flow.async_configure(
            result4["flow_id"],
            user_input={config_flow.OVERWRITE_COORDINATOR_IEEE: True},
        )

        result5 = await consume_progress_flow(
            hass,
            flow_id=confirm_result["flow_id"],
            valid_step_ids=("restore_backup",),
        )

        # Prompt user to plug new adapter back in again
        assert result5["type"] is FlowResultType.FORM
        assert result5["step_id"] == "plug_in_new_radio"
        assert result5["description_placeholders"] == {"device_path": "/dev/ttyUSB1234"}

        # User confirms they plugged in the adapter
        final_retry_result = await hass.config_entries.flow.async_configure(
            result5["flow_id"],
            user_input={},
        )

        result6 = await consume_progress_flow(
            hass,
            flow_id=final_retry_result["flow_id"],
            valid_step_ids=("restore_backup",),
        )

    # Entry created successfully
    assert result6["type"] is FlowResultType.CREATE_ENTRY
    assert result6["data"][CONF_RADIO_TYPE] == "ezsp"

    # Verify restore was attempted four times:
    # first fail + retry for destructive dialog + failed destructive + successful retry
    assert mock_restore_backup.call_count == 4