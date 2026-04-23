async def test_formation_strategy_restore_manual_backup_overwrite_ieee_ezsp_write_fail(
    allow_overwrite_ieee_mock,
    advanced_pick_radio: RadioPicker,
    mock_app: AsyncMock,
    backup,
    hass: HomeAssistant,
) -> None:
    """Test restoring a manual backup on EZSP coordinators (overwrite IEEE) with a write failure."""
    advanced_strategy_result = await advanced_pick_radio(RadioType.ezsp)

    upload_backup_result = await hass.config_entries.flow.async_configure(
        advanced_strategy_result["flow_id"],
        user_input={"next_step_id": config_flow.FORMATION_UPLOAD_MANUAL_BACKUP},
    )
    await hass.async_block_till_done()

    assert upload_backup_result["type"] is FlowResultType.FORM
    assert upload_backup_result["step_id"] == "upload_manual_backup"

    with (
        patch(
            "homeassistant.components.zha.config_flow.ZhaConfigFlowHandler._parse_uploaded_backup",
            return_value=backup,
        ),
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager.restore_backup",
            new_callable=DelayedAsyncMock,
            side_effect=[
                DestructiveWriteNetworkSettings("Radio IEEE change is permanent"),
                CannotWriteNetworkSettings("Failed to write settings"),
            ],
        ) as mock_restore_backup,
    ):
        result_upload = await hass.config_entries.flow.async_configure(
            upload_backup_result["flow_id"],
            user_input={config_flow.UPLOADED_BACKUP_FILE: str(uuid.uuid4())},
        )

        confirm_restore_result = await consume_progress_flow(
            hass,
            flow_id=result_upload["flow_id"],
            valid_step_ids=("restore_backup",),
        )

        assert mock_restore_backup.call_count == 1
        assert not mock_restore_backup.mock_calls[0].kwargs.get("overwrite_ieee")
        mock_restore_backup.reset_mock()

        # The radio requires user confirmation for restore
        assert confirm_restore_result["type"] is FlowResultType.FORM
        assert confirm_restore_result["step_id"] == "confirm_ezsp_ieee_overwrite"

        confirm_result = await hass.config_entries.flow.async_configure(
            confirm_restore_result["flow_id"],
            user_input={config_flow.OVERWRITE_COORDINATOR_IEEE: True},
        )

        final_result = await consume_progress_flow(
            hass,
            flow_id=confirm_result["flow_id"],
            valid_step_ids=("restore_backup",),
        )

    assert final_result["type"] is FlowResultType.ABORT
    assert final_result["reason"] == "cannot_restore_backup"
    assert (
        "Failed to write settings" in final_result["description_placeholders"]["error"]
    )

    assert mock_restore_backup.call_count == 1
    assert mock_restore_backup.mock_calls[0].kwargs["overwrite_ieee"] is True