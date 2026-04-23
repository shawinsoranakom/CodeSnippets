async def test_option_flow_flasher_addon_flash_failure(
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
    """Test where flasher addon fails to flash Zigbee firmware."""

    addon_info.return_value.options["device"] = "/dev/ttyTEST123"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=TEST_DOMAIN,
        options={},
        title="Test HW",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "addon_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "uninstall_addon"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "uninstall_addon"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {silabs_multiprotocol_addon.CONF_DISABLE_MULTI_PAN: True}
    )
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "uninstall_multiprotocol_addon"
    assert result["progress_action"] == "uninstall_multiprotocol_addon"

    start_addon.side_effect = SupervisorError("Boom")

    await hass.async_block_till_done()
    uninstall_addon.assert_called_once_with("core_silabs_multiprotocol")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_flasher_addon"
    assert result["progress_action"] == "start_flasher_addon"
    assert result["description_placeholders"] == {"addon_name": "Silicon Labs Flasher"}

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_start_failed"
    assert result["description_placeholders"]["addon_name"] == "Silicon Labs Flasher"