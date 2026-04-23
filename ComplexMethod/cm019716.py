async def test_update_entity_installation(
    hass: HomeAssistant, update_config_entry: ConfigEntry
) -> None:
    """Test the Hardware firmware update entity installation."""

    assert await hass.config_entries.async_setup(update_config_entry.entry_id)
    await hass.async_block_till_done()

    # Set up another integration communicating with the device
    owning_config_entry = MockConfigEntry(
        domain="another_integration",
        data={
            "device": {
                "path": TEST_DEVICE,
                "flow_control": "hardware",
                "baudrate": 115200,
            },
            "radio_type": "ezsp",
        },
        version=4,
    )
    owning_config_entry.add_to_hass(hass)
    owning_config_entry.mock_state(hass, ConfigEntryState.LOADED)

    # The integration provides firmware info
    mock_hw_module = Mock()
    mock_hw_module.get_firmware_info = lambda hass, config_entry: FirmwareInfo(
        device=TEST_DEVICE,
        firmware_type=ApplicationType.EZSP,
        firmware_version="7.3.1.0 build 0",
        owners=[OwningIntegration(config_entry_id=config_entry.entry_id)],
        source="another_integration",
    )

    async_register_firmware_info_provider(hass, "another_integration", mock_hw_module)

    # Pretend the other integration loaded and notified hardware of the running firmware
    await async_notify_firmware_info(
        hass,
        "another_integration",
        mock_hw_module.get_firmware_info(hass, owning_config_entry),
    )

    state = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["title"] == "EmberZNet"
    assert state.attributes["installed_version"] == "7.3.1.0"
    assert state.attributes["latest_version"] == "7.4.4.0"
    assert state.attributes["release_summary"] == ("Some release notes go here")
    assert state.attributes["release_url"] == ("https://example.org/release_notes")

    async def mock_flash_firmware(
        hass: HomeAssistant,
        device: str,
        fw_data: bytes,
        flasher_cls: type[DeviceSpecificFlasher],
        expected_installed_firmware_type: ApplicationType,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> FirmwareInfo:
        await asyncio.sleep(0)
        progress_callback(0, 100)
        await asyncio.sleep(0)
        progress_callback(50, 100)
        await asyncio.sleep(0)
        progress_callback(100, 100)

        return FirmwareInfo(
            device=TEST_DEVICE,
            firmware_type=ApplicationType.EZSP,
            firmware_version="7.4.4.0 build 0",
            owners=[],
            source="probe",
        )

    # When we install it, the other integration is reloaded
    with (
        patch(
            "homeassistant.components.homeassistant_hardware.update.async_flash_silabs_firmware",
            side_effect=mock_flash_firmware,
        ),
    ):
        state_changes: list[Event[EventStateChangedData]] = async_capture_events(
            hass, EVENT_STATE_CHANGED
        )
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": TEST_UPDATE_ENTITY_ID},
            blocking=True,
        )

    # Progress events are emitted during the installation
    assert len(state_changes) == 7

    # Indeterminate progress first
    assert state_changes[0].data["new_state"].attributes["in_progress"] is True
    assert state_changes[0].data["new_state"].attributes["update_percentage"] is None

    # Then the update starts
    assert state_changes[1].data["new_state"].attributes["update_percentage"] == 0
    assert state_changes[2].data["new_state"].attributes["update_percentage"] == 50
    assert state_changes[3].data["new_state"].attributes["update_percentage"] == 100

    # Once it is done, we probe the firmware
    assert state_changes[4].data["new_state"].attributes["in_progress"] is True
    assert state_changes[4].data["new_state"].attributes["update_percentage"] is None

    # Finally, the update finishes
    assert state_changes[5].data["new_state"].attributes["update_percentage"] is None
    assert state_changes[6].data["new_state"].attributes["update_percentage"] is None
    assert state_changes[6].data["new_state"].attributes["in_progress"] is False

    # After the firmware update, the entity has the new version and the correct state
    state_after_install = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state_after_install is not None
    assert state_after_install.state == "off"
    assert state_after_install.attributes["title"] == "EmberZNet"
    assert state_after_install.attributes["installed_version"] == "7.4.4.0"
    assert state_after_install.attributes["latest_version"] == "7.4.4.0"