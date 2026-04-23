async def test_firmware_options_flow_zigbee(hass: HomeAssistant) -> None:
    """Test the firmware options flow for Yellow."""
    fw_type = ApplicationType.EZSP
    fw_version = "7.4.4.0 build 0"
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    config_entry = MockConfigEntry(
        data={"firmware": ApplicationType.SPINEL},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)

    # First step is confirmation
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "main_menu"
    assert "firmware_settings" in result["menu_options"]

    # Pick firmware settings
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "firmware_settings"},
    )

    assert result["step_id"] == "pick_firmware"
    description_placeholders = result["description_placeholders"]
    assert description_placeholders is not None
    assert description_placeholders["firmware_type"] == "spinel"
    assert description_placeholders["model"] == "Home Assistant Yellow"

    mock_update_client = AsyncMock()
    mock_manifest = Mock()
    mock_firmware = Mock()
    mock_firmware.filename = "yellow_zigbee_ncp_7.4.4.0.gbl"
    mock_firmware.metadata = {
        "ezsp_version": "7.4.4.0",
        "fw_type": "yellow_zigbee_ncp",
        "metadata_version": 2,
    }
    mock_manifest.firmwares = [mock_firmware]
    mock_update_client.async_update_data.return_value = mock_manifest
    mock_update_client.async_fetch_firmware.return_value = b"firmware_data"

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.guess_hardware_owners",
            return_value=[],
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.FirmwareUpdateClient",
            return_value=mock_update_client,
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.async_flash_silabs_firmware",
            return_value=FirmwareInfo(
                device=RADIO_DEVICE,
                firmware_type=fw_type,
                firmware_version=fw_version,
                owners=[],
                source="probe",
            ),
        ) as flash_mock,
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.probe_silabs_firmware_info",
            side_effect=[
                # First call: probe before installation (returns current SPINEL firmware)
                FirmwareInfo(
                    device=RADIO_DEVICE,
                    firmware_type=ApplicationType.SPINEL,
                    firmware_version="2.4.4.0",
                    owners=[],
                    source="probe",
                ),
                # Second call: probe after installation (returns new EZSP firmware)
                FirmwareInfo(
                    device=RADIO_DEVICE,
                    firmware_type=fw_type,
                    firmware_version=fw_version,
                    owners=[],
                    source="probe",
                ),
            ],
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.util.parse_firmware_image"
        ),
    ):
        pick_result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        assert pick_result["type"] is FlowResultType.MENU
        assert pick_result["step_id"] == "zigbee_installation_type"

        create_result = await hass.config_entries.options.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

    assert create_result["type"] is FlowResultType.CREATE_ENTRY

    assert config_entry.data == {
        "firmware": fw_type.value,
        "firmware_version": fw_version,
    }

    assert flash_mock.mock_calls == [
        call(
            hass=hass,
            device=RADIO_DEVICE,
            fw_data=ANY,
            flasher_cls=YellowFlasher,
            expected_installed_firmware_type=ApplicationType.EZSP,
            progress_callback=ANY,
        )
    ]