async def test_options_flow(
    usb_data: UsbServiceInfo, model: str, hass: HomeAssistant
) -> None:
    """Test the options flow for Connect ZBT-2."""
    config_entry = MockConfigEntry(
        domain="homeassistant_connect_zbt2",
        data={
            "firmware": "spinel",
            "firmware_version": "SL-OPENTHREAD/2.4.4.0_GitHub-7074a43e4",
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        },
        version=1,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)

    # First step is confirmation
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pick_firmware"
    description_placeholders = result["description_placeholders"]
    assert description_placeholders is not None
    assert description_placeholders["firmware_type"] == "spinel"
    assert description_placeholders["model"] == model

    mock_update_client = AsyncMock()
    mock_manifest = Mock()
    mock_firmware = Mock()
    mock_firmware.filename = "zbt2_zigbee_ncp_7.4.4.0.gbl"
    mock_firmware.metadata = {
        "ezsp_version": "7.4.4.0",
        "fw_type": "zbt2_zigbee_ncp",
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
                device=usb_data.device,
                firmware_type=ApplicationType.EZSP,
                firmware_version="7.4.4.0 build 0",
                owners=[],
                source="probe",
            ),
        ) as flash_mock,
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.probe_silabs_firmware_info",
            side_effect=[
                # First call: probe before installation (returns current SPINEL firmware)
                FirmwareInfo(
                    device=usb_data.device,
                    firmware_type=ApplicationType.SPINEL,
                    firmware_version="2.4.4.0",
                    owners=[],
                    source="probe",
                ),
                # Second call: probe after installation (returns new EZSP firmware)
                FirmwareInfo(
                    device=usb_data.device,
                    firmware_type=ApplicationType.EZSP,
                    firmware_version="7.4.4.0 build 0",
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
        "firmware": "ezsp",
        "firmware_version": "7.4.4.0 build 0",
        "device": usb_data.device,
        "manufacturer": usb_data.manufacturer,
        "pid": usb_data.pid,
        "product": usb_data.description,
        "serial_number": usb_data.serial_number,
        "vid": usb_data.vid,
    }

    assert flash_mock.mock_calls == [
        call(
            hass=hass,
            device=USB_DATA_ZBT2.device,
            fw_data=ANY,
            flasher_cls=Zbt2Flasher,
            expected_installed_firmware_type=ApplicationType.EZSP,
            progress_callback=ANY,
        )
    ]

    flows = hass.config_entries.flow.async_progress()

    # Ensure a ZHA discovery flow has been created
    assert len(flows) == 1
    zha_flow = flows[0]
    assert zha_flow["handler"] == "zha"
    assert zha_flow["context"]["source"] == "hardware"
    assert zha_flow["step_id"] == "confirm"

    progress_zha_flows = hass.config_entries.flow._async_progress_by_handler(
        handler="zha",
        match_context=None,
    )

    assert len(progress_zha_flows) == 1

    # Ensure correct baudrate
    progress_zha_flow = progress_zha_flows[0]
    assert progress_zha_flow.init_data == {
        "flow_strategy": "recommended",
        "name": model,
        "port": {
            "path": usb_data.device,
            "baudrate": 460800,
            "flow_control": "hardware",
        },
        "radio_type": "ezsp",
    }