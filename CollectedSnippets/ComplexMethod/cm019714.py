async def test_options_flow_zigbee_to_thread(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test the options flow, migrating Zigbee to Thread."""
    config_entry = MockConfigEntry(
        domain=TEST_DOMAIN,
        data={
            "firmware": "ezsp",
            "device": TEST_DEVICE,
            "hardware": TEST_HARDWARE_NAME,
        },
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)

    with mock_firmware_info(
        probe_app_type=ApplicationType.EZSP,
        flash_app_type=ApplicationType.SPINEL,
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] is FlowResultType.MENU
        assert result["step_id"] == "pick_firmware"
        assert result["description_placeholders"] == {
            "firmware_type": "ezsp",
            "model": TEST_HARDWARE_NAME,
            "firmware_name": "unknown",
        }

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "install_thread_firmware"
        assert result["progress_action"] == "install_firmware"

        await hass.async_block_till_done(wait_background_tasks=True)

        result = await hass.config_entries.options.async_configure(result["flow_id"])

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "install_otbr_addon"
        assert result["progress_action"] == "install_otbr_addon"

        await hass.async_block_till_done(wait_background_tasks=True)

        result = await hass.config_entries.options.async_configure(result["flow_id"])

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "start_otbr_addon"
        assert result["progress_action"] == "start_otbr_addon"

        await hass.async_block_till_done(wait_background_tasks=True)

        result = await hass.config_entries.options.async_configure(result["flow_id"])

    assert install_addon.call_count == 1
    assert install_addon.call_args == call("core_openthread_border_router")
    assert set_addon_options.call_count == 1
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
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # The firmware type has been updated
    assert config_entry.data["firmware"] == "spinel"