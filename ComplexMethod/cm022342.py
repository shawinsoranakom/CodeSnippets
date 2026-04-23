async def test_firmware_options_flow_thread(
    hass: HomeAssistant, start_addon: AsyncMock
) -> None:
    """Test the firmware options flow for Yellow with Thread."""
    fw_type = ApplicationType.SPINEL
    fw_version = "2.4.4.0"
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
            device=RADIO_DEVICE,
            firmware_type=expected_installed_firmware_type,
            firmware_version=fw_version,
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
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.BaseFirmwareInstallFlow._install_firmware_step",
            autospec=True,
            side_effect=mock_install_firmware_step,
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_THREAD},
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "start_otbr_addon"

        # Make sure the flow continues when the progress task is done.
        await hass.async_block_till_done()

        create_result = await hass.config_entries.options.async_configure(
            result["flow_id"]
        )

    assert start_addon.call_count == 1
    assert start_addon.call_args == call("core_openthread_border_router")
    assert create_result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.data == {
        "firmware": fw_type.value,
        "firmware_version": fw_version,
    }