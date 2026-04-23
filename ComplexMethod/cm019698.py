async def test_option_flow_addon_installed_same_device_uninstall(
    hass: HomeAssistant,
    addon_info,
    addon_store_info,
    addon_installed,
    install_addon,
    start_addon,
    stop_addon,
    uninstall_addon,
    set_addon_options,
    options_flow_poll_addon_state,
) -> None:
    """Test uninstalling the multi pan addon."""

    addon_info.return_value.options["device"] = "/dev/ttyTEST123"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=TEST_DOMAIN,
        options={},
        title="Test HW",
    )
    config_entry.add_to_hass(hass)

    zha_config_entry = MockConfigEntry(
        data={
            "device": {"path": "socket://core-silabs-multiprotocol:9999"},
            "radio_type": "ezsp",
        },
        domain=ZHA_DOMAIN,
        options={},
        title="Test Multiprotocol",
    )
    zha_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "addon_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "uninstall_addon"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "uninstall_addon"

    # Make sure the flasher addon is installed
    addon_store_info.return_value.installed = False
    addon_store_info.return_Value.available = True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {silabs_multiprotocol_addon.CONF_DISABLE_MULTI_PAN: True}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_flasher_addon"
    assert result["progress_action"] == "install_addon"

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "uninstall_multiprotocol_addon"
    assert result["progress_action"] == "uninstall_multiprotocol_addon"

    await hass.async_block_till_done()
    uninstall_addon.assert_called_once_with("core_silabs_multiprotocol")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_flasher_addon"
    assert result["progress_action"] == "start_flasher_addon"
    assert result["description_placeholders"] == {"addon_name": "Silicon Labs Flasher"}

    await hass.async_block_till_done()
    install_addon.assert_called_once_with("core_silabs_flasher")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Check the ZHA config entry data is updated
    assert zha_config_entry.data == {
        "device": {
            "path": "/dev/ttyTEST123",
            "baudrate": 115200,
            "flow_control": "hardware",
        },
        "radio_type": "ezsp",
    }
    assert zha_config_entry.title == "Test"