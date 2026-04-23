async def test_option_flow_uninstall_migration_finish_failure(
    mock_finish_migration,
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
    """Test uninstalling the multi pan addon, case where ZHA migration init fails."""

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

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {silabs_multiprotocol_addon.CONF_DISABLE_MULTI_PAN: True}
    )

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
    assert result["reason"] == "zha_migration_failed"