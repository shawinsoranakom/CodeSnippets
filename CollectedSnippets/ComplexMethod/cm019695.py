async def test_option_flow_install_multi_pan_addon_zha_other_radio(
    hass: HomeAssistant,
    addon_store_info,
    addon_info,
    install_addon,
    set_addon_options,
    start_addon,
    options_flow_poll_addon_state,
) -> None:
    """Test installing the multi pan addon when a zha config entry exists."""

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
            "device": {
                "path": "/dev/other_radio",
                "baudrate": 115200,
                "flow_control": "hardware",
            },
            "radio_type": "ezsp",
        },
        domain=ZHA_DOMAIN,
        options={},
        title="Test HW",
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

    addon_info.return_value.hostname = "core-silabs-multiprotocol"
    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"
    set_addon_options.assert_called_once_with(
        "core_silabs_multiprotocol",
        AddonsOptions(
            config={
                "autoflash_firmware": True,
                "device": "/dev/ttyTEST123",
                "baudrate": "115200",
                "flow_control": True,
            }
        ),
    )

    await hass.async_block_till_done()
    start_addon.assert_called_once_with("core_silabs_multiprotocol")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Check the ZHA entry data is not changed
    assert zha_config_entry.data == {
        "device": {
            "path": "/dev/other_radio",
            "baudrate": 115200,
            "flow_control": "hardware",
        },
        "radio_type": "ezsp",
    }