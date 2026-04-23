async def test_options_flow_thread_to_zigbee(hass: HomeAssistant) -> None:
    """Test the options flow, migrating Thread to Zigbee."""
    config_entry = MockConfigEntry(
        domain=TEST_DOMAIN,
        data={
            "firmware": "spinel",
            "device": TEST_DEVICE,
            "hardware": TEST_HARDWARE_NAME,
        },
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pick_firmware"
    assert result["description_placeholders"] == {
        "firmware_type": "spinel",
        "model": TEST_HARDWARE_NAME,
        "firmware_name": "unknown",
    }

    with mock_firmware_info(
        probe_app_type=ApplicationType.SPINEL,
    ):
        pick_result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        assert pick_result["type"] is FlowResultType.MENU
        assert pick_result["step_id"] == "zigbee_installation_type"

    with mock_firmware_info(
        probe_app_type=ApplicationType.EZSP,
    ):
        # We are now done
        result = await hass.config_entries.options.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "install_zigbee_firmware"
        assert result["progress_action"] == "install_firmware"

        await hass.async_block_till_done(wait_background_tasks=True)

        create_result = await hass.config_entries.options.async_configure(
            result["flow_id"]
        )

        assert create_result["type"] is FlowResultType.CREATE_ENTRY

        # The firmware type has been updated
        assert config_entry.data["firmware"] == "ezsp"