async def test_config_flow_zigbee(hass: HomeAssistant) -> None:
    """Test Zigbee config flow for Connect ZBT-2."""
    fw_type = ApplicationType.EZSP
    fw_version = "7.4.4.0 build 0"
    model = "Home Assistant Connect ZBT-2"
    usb_data = USB_DATA_ZBT2

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "usb"}, data=usb_data
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pick_firmware"
    description_placeholders = result["description_placeholders"]
    assert description_placeholders is not None
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
            firmware_version=fw_version,
            owners=[],
            source="probe",
        )
        return await getattr(self, f"async_step_{next_step_id}")()

    with (
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.BaseFirmwareConfigFlow._install_firmware_step",
            autospec=True,
            side_effect=mock_install_firmware_step,
        ),
    ):
        pick_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        assert pick_result["type"] is FlowResultType.MENU
        assert pick_result["step_id"] == "zigbee_installation_type"

        create_result = await hass.config_entries.flow.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

    assert create_result["type"] is FlowResultType.CREATE_ENTRY
    config_entry = create_result["result"]
    assert config_entry.data == {
        "firmware": fw_type.value,
        "firmware_version": fw_version,
        "device": usb_data.device,
        "manufacturer": usb_data.manufacturer,
        "pid": usb_data.pid,
        "product": usb_data.description,
        "serial_number": usb_data.serial_number,
        "vid": usb_data.vid,
    }

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
        "radio_type": fw_type.value,
    }