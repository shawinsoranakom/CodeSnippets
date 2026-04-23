async def test_options_flow(
    usb_data: UsbServiceInfo, model: str, hass: HomeAssistant
) -> None:
    """Test the options flow for SkyConnect."""
    config_entry = MockConfigEntry(
        domain="homeassistant_sky_connect",
        data={
            "firmware": "spinel",
            "device": usb_data.device,
            "manufacturer": usb_data.manufacturer,
            "pid": usb_data.pid,
            "description": usb_data.description,
            "product": usb_data.description,
            "serial_number": usb_data.serial_number,
            "vid": usb_data.vid,
        },
        version=1,
        minor_version=2,
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

    async def mock_install_firmware_step(
        self,
        fw_update_url: str,
        fw_type: str,
        firmware_name: str,
        expected_installed_firmware_type: ApplicationType,
        step_id: str,
        next_step_id: str,
    ) -> ConfigFlowResult:
        self._probed_firmware_info = FirmwareInfo(
            device=usb_data.device,
            firmware_type=expected_installed_firmware_type,
            firmware_version="7.4.4.0 build 0",
            owners=[],
            source="probe",
        )
        return await getattr(self, f"async_step_{next_step_id}")()

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.guess_hardware_owners",
            return_value=[],
        ),
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.BaseFirmwareOptionsFlow._install_firmware_step",
            autospec=True,
            side_effect=mock_install_firmware_step,
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
        "description": usb_data.description,
        "product": usb_data.description,
        "serial_number": usb_data.serial_number,
        "vid": usb_data.vid,
    }