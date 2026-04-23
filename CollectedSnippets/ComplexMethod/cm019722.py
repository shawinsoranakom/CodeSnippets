async def test_config_flow_thread_addon_info_fails(
    hass: HomeAssistant,
    addon_store_info: AsyncMock,
) -> None:
    """Test addon info fails before firmware install."""

    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": "hardware"}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pick_firmware"

    with mock_firmware_info(
        probe_app_type=ApplicationType.EZSP,
        flash_app_type=ApplicationType.SPINEL,
    ):
        addon_store_info.side_effect = AddonError()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "install_thread_firmware"

        result = await consume_progress_flow(
            hass,
            flow_id=result["flow_id"],
            valid_step_ids=("install_thread_firmware",),
        )

        # Cannot get addon info
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "addon_info_failed"
        assert result["description_placeholders"] == {
            "model": TEST_HARDWARE_NAME,
            "firmware_type": "spinel",
            "firmware_name": "Thread",
            "addon_name": "OpenThread Border Router",
        }