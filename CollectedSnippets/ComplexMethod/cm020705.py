async def test_formation_strategy_restore_manual_backup_overwrite_ieee_ezsp(
    allow_overwrite_ieee_mock,
    advanced_pick_radio: RadioPicker,
    mock_app: AsyncMock,
    backup,
    hass: HomeAssistant,
) -> None:
    """Test restoring a manual backup on EZSP coordinators (overwrite IEEE)."""
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
                DestructiveWriteNetworkSettings("Radio IEEE change is permanent"),
                None,
            ],
        ) as mock_restore_backup,
    ):
        result_upload = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={config_flow.UPLOADED_BACKUP_FILE: str(uuid.uuid4())},
        )

        result3 = await consume_progress_flow(
            hass,
            flow_id=result_upload["flow_id"],
            valid_step_ids=("restore_backup",),
        )

        assert mock_restore_backup.call_count == 1
        assert not mock_restore_backup.mock_calls[0].kwargs.get("overwrite_ieee")
        mock_restore_backup.reset_mock()

        # The radio requires user confirmation for restore
        assert result3["type"] is FlowResultType.FORM
        assert result3["step_id"] == "confirm_ezsp_ieee_overwrite"

        result_confirm = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            user_input={config_flow.OVERWRITE_COORDINATOR_IEEE: True},
        )

        result_final = await consume_progress_flow(
            hass,
            flow_id=result_confirm["flow_id"],
            valid_step_ids=("restore_backup",),
        )

    assert result_final["type"] is FlowResultType.CREATE_ENTRY
    assert result_final["data"][CONF_RADIO_TYPE] == "ezsp"

    assert mock_restore_backup.call_count == 1
    assert mock_restore_backup.mock_calls[0].kwargs["overwrite_ieee"] is True