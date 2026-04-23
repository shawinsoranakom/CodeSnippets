async def test_config_flow_thread(
    usb_data: UsbServiceInfo,
    model: str,
    hass: HomeAssistant,
    start_addon: AsyncMock,
) -> None:
    """Test the config flow for SkyConnect with Thread."""
    fw_type = ApplicationType.SPINEL
    fw_version = "2.4.4.0"

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
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "start_otbr_addon"

        # Make sure the flow continues when the progress task is done.
        await hass.async_block_till_done()

        create_result = await hass.config_entries.flow.async_configure(
            result["flow_id"]
        )

    assert start_addon.call_count == 1
    assert start_addon.call_args == call("core_openthread_border_router")
    assert create_result["type"] is FlowResultType.CREATE_ENTRY
    config_entry = create_result["result"]
    assert config_entry.data == {
        "firmware": fw_type.value,
        "firmware_version": fw_version,
        "device": usb_data.device,
        "manufacturer": usb_data.manufacturer,
        "pid": usb_data.pid,
        "description": usb_data.description,
        "product": usb_data.description,
        "serial_number": usb_data.serial_number,
        "vid": usb_data.vid,
    }

    flows = hass.config_entries.flow.async_progress()

    assert len(flows) == 0