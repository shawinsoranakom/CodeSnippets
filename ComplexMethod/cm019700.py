async def test_option_flow_flasher_install_failure(
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
    """Test uninstalling the multi pan addon, case where flasher addon fails."""

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

    addon_store_info.return_value.installed = False
    addon_store_info.return_value.available = True
    install_addon.side_effect = [AddonError()]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {silabs_multiprotocol_addon.CONF_DISABLE_MULTI_PAN: True}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_flasher_addon"
    assert result["progress_action"] == "install_addon"

    await hass.async_block_till_done()
    install_addon.assert_called_once_with("core_silabs_flasher")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_install_failed"