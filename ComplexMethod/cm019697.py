async def test_option_flow_addon_installed_same_device_reconfigure_expected_users(
    hass: HomeAssistant,
    addon_info,
    addon_store_info,
    addon_installed,
    configured_channel: int | None,
    suggested_channel: int,
) -> None:
    """Test reconfiguring the multi pan addon."""

    addon_info.return_value.options["device"] = "/dev/ttyTEST123"

    multipan_manager = await silabs_multiprotocol_addon.get_multiprotocol_addon_manager(
        hass
    )
    multipan_manager._channel = configured_channel

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=TEST_DOMAIN,
        options={},
        title="Test HW",
    )
    config_entry.add_to_hass(hass)

    mock_multiprotocol_platforms = {}
    for domain in ("otbr", "zha"):
        mock_multiprotocol_platform = MockMultiprotocolPlatform()
        mock_multiprotocol_platforms[domain] = mock_multiprotocol_platform
        mock_multiprotocol_platform.channel = configured_channel
        mock_multiprotocol_platform.using_multipan = True

        hass.config.components.add(domain)
        mock_platform(
            hass, f"{domain}.silabs_multiprotocol", mock_multiprotocol_platform
        )
        hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: domain})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "addon_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "reconfigure_addon"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "change_channel"
    assert get_suggested(result["data_schema"].schema, "channel") == suggested_channel

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"channel": "14"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "notify_channel_change"
    assert result["description_placeholders"] == {"delay_minutes": "5"}

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY

    for domain in ("otbr", "zha"):
        assert mock_multiprotocol_platforms[domain].change_channel_calls == [(14, 300)]
    assert multipan_manager._channel == 14