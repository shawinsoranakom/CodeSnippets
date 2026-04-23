async def test_option_flow_install_multi_pan_addon_zha_migration_fails_step_1(
    mock_initiate_migration,
    hass: HomeAssistant,
    addon_store_info,
    addon_info,
    install_addon,
    set_addon_options,
    start_addon,
) -> None:
    """Test installing the multi pan addon."""

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=TEST_DOMAIN,
        options={},
        title="Test HW",
    )
    config_entry.add_to_hass(hass)

    zha_config_entry = MockConfigEntry(
        data={"device": {"path": "/dev/ttyTEST123"}, "radio_type": "ezsp"},
        domain=ZHA_DOMAIN,
        options={},
        title="Test",
    )
    zha_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "addon_not_installed"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "enable_multi_pan": True,
        },
    )
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_addon"
    assert result["progress_action"] == "install_addon"

    await hass.async_block_till_done()
    install_addon.assert_called_once_with("core_silabs_multiprotocol")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "zha_migration_failed"
    set_addon_options.assert_not_called()