async def test_addon_options_changed(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    addon_options: dict[str, Any],
    start_addon: AsyncMock,
    old_device: str,
    new_device: str,
    old_s0_legacy_key: str,
    new_s0_legacy_key: str,
    old_s2_access_control_key: str,
    new_s2_access_control_key: str,
    old_s2_authenticated_key: str,
    new_s2_authenticated_key: str,
    old_s2_unauthenticated_key: str,
    new_s2_unauthenticated_key: str,
    old_lr_s2_access_control_key: str,
    new_lr_s2_access_control_key: str,
    old_lr_s2_authenticated_key: str,
    new_lr_s2_authenticated_key: str,
) -> None:
    """Test update config entry data on entry setup if add-on options changed."""
    addon_options["device"] = new_device
    addon_options["s0_legacy_key"] = new_s0_legacy_key
    addon_options["s2_access_control_key"] = new_s2_access_control_key
    addon_options["s2_authenticated_key"] = new_s2_authenticated_key
    addon_options["s2_unauthenticated_key"] = new_s2_unauthenticated_key
    addon_options["lr_s2_access_control_key"] = new_lr_s2_access_control_key
    addon_options["lr_s2_authenticated_key"] = new_lr_s2_authenticated_key
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://host1:3001",
            "use_addon": True,
            "usb_path": old_device,
            "s0_legacy_key": old_s0_legacy_key,
            "s2_access_control_key": old_s2_access_control_key,
            "s2_authenticated_key": old_s2_authenticated_key,
            "s2_unauthenticated_key": old_s2_unauthenticated_key,
            "lr_s2_access_control_key": old_lr_s2_access_control_key,
            "lr_s2_authenticated_key": old_lr_s2_authenticated_key,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.data["usb_path"] == new_device
    assert entry.data["s0_legacy_key"] == new_s0_legacy_key
    assert entry.data["s2_access_control_key"] == new_s2_access_control_key
    assert entry.data["s2_authenticated_key"] == new_s2_authenticated_key
    assert entry.data["s2_unauthenticated_key"] == new_s2_unauthenticated_key
    assert entry.data["lr_s2_access_control_key"] == new_lr_s2_access_control_key
    assert entry.data["lr_s2_authenticated_key"] == new_lr_s2_authenticated_key
    assert install_addon.call_count == 0
    assert start_addon.call_count == 0