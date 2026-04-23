async def test_config_flow_thread(
    hass: HomeAssistant,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test the config flow."""
    init_result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": "hardware"}
    )

    assert init_result["type"] is FlowResultType.MENU
    assert init_result["step_id"] == "pick_firmware"

    with mock_firmware_info(
        probe_app_type=ApplicationType.EZSP,
        flash_app_type=ApplicationType.SPINEL,
    ):
        # Pick the menu option
        pick_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        assert pick_result["type"] is FlowResultType.SHOW_PROGRESS
        assert pick_result["progress_action"] == "install_firmware"
        assert pick_result["step_id"] == "install_thread_firmware"
        assert pick_result["description_placeholders"] == {
            "firmware_type": "ezsp",
            "model": TEST_HARDWARE_NAME,
            "firmware_name": "Thread",
        }

        await hass.async_block_till_done(wait_background_tasks=True)

        # Progress the flow, it is now installing firmware
        create_result = await consume_progress_flow(
            hass,
            flow_id=pick_result["flow_id"],
            valid_step_ids=(
                "pick_firmware_thread",
                "install_otbr_addon",
                "install_thread_firmware",
                "start_otbr_addon",
            ),
        )

        # Installation will conclude with the config entry being created
        assert create_result["type"] is FlowResultType.CREATE_ENTRY

        config_entry = create_result["result"]
        assert config_entry.data == {
            "firmware": "spinel",
            "device": TEST_DEVICE,
            "hardware": TEST_HARDWARE_NAME,
        }

        assert set_addon_options.call_args == call(
            "core_openthread_border_router",
            AddonsOptions(
                config={
                    "device": "/dev/SomeDevice123",
                    "baudrate": 460800,
                    "flow_control": True,
                    "autoflash_firmware": False,
                },
            ),
        )
        assert start_addon.call_count == 1
        assert start_addon.call_args == call("core_openthread_border_router")