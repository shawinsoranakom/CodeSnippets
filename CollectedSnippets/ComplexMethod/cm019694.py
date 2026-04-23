async def test_option_flow_install_multi_pan_addon_zha(
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
                "path": "/dev/ttyTEST123",
                "baudrate": 115200,
                "flow_control": None,
            },
            "radio_type": "ezsp",
        },
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

    multipan_manager = await silabs_multiprotocol_addon.get_multiprotocol_addon_manager(
        hass
    )
    assert multipan_manager._channel is None
    with patch(
        "homeassistant.components.zha.silabs_multiprotocol.async_get_channel",
        return_value=11,
    ):
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
    # Check the channel is initialized from ZHA
    assert multipan_manager._channel == 11
    # Check the ZHA config entry data is updated
    assert zha_config_entry.data == {
        "device": {
            "path": "socket://core-silabs-multiprotocol:9999",
            "baudrate": 115200,
            "flow_control": None,
        },
        "radio_type": "ezsp",
    }
    assert zha_config_entry.title == "Test Multiprotocol"

    await hass.async_block_till_done()
    start_addon.assert_called_once_with("core_silabs_multiprotocol")

    result = await hass.config_entries.options.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY