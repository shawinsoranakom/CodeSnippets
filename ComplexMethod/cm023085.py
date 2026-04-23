async def test_install_addon(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test install and start the Z-Wave JS add-on during entry setup."""
    device = "/test"
    s0_legacy_key = "s0_legacy"
    s2_access_control_key = "s2_access_control"
    s2_authenticated_key = "s2_authenticated"
    s2_unauthenticated_key = "s2_unauthenticated"
    addon_options = {
        "device": device,
        "s0_legacy_key": s0_legacy_key,
        "s2_access_control_key": s2_access_control_key,
        "s2_authenticated_key": s2_authenticated_key,
        "s2_unauthenticated_key": s2_unauthenticated_key,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "use_addon": True,
            "usb_path": device,
            "s0_legacy_key": s0_legacy_key,
            "s2_access_control_key": s2_access_control_key,
            "s2_authenticated_key": s2_authenticated_key,
            "s2_unauthenticated_key": s2_unauthenticated_key,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 1
    assert install_addon.call_args == call("core_zwave_js")
    assert set_addon_options.call_count == 1
    assert set_addon_options.call_args == call(
        "core_zwave_js", AddonsOptions(config=addon_options)
    )
    assert start_addon.call_count == 1
    assert start_addon.call_args == call("core_zwave_js")