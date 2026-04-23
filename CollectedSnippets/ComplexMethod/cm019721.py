async def test_config_flow_thread_not_hassio(hass: HomeAssistant) -> None:
    """Test when the stick is used with a non-hassio setup and Thread is selected."""
    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": "hardware"}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pick_firmware"

    with mock_firmware_info(
        is_hassio=False,
        probe_app_type=ApplicationType.EZSP,
        flash_app_type=ApplicationType.SPINEL,
    ):
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

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "not_hassio_thread"
        assert result["description_placeholders"] == {
            "model": TEST_HARDWARE_NAME,
            "firmware_type": "spinel",
            "firmware_name": "Thread",
        }