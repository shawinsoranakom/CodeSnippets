async def test_update(hass: HomeAssistant) -> None:
    """Tests update entity."""
    mocked_hole = _create_mocked_hole(api_version=6)
    entry = MockConfigEntry(domain=pi_hole.DOMAIN, data=CONFIG_DATA_DEFAULTS)
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole):
        assert await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()

    state = hass.states.get("update.pi_hole_core_update_available")
    assert state.name == "Pi-Hole Core update available"
    assert state.state == STATE_ON
    assert state.attributes["installed_version"] == "v5.5"
    assert state.attributes["latest_version"] == "v5.6"
    assert (
        state.attributes["release_url"]
        == "https://github.com/pi-hole/pi-hole/releases/tag/v5.6"
    )

    state = hass.states.get("update.pi_hole_ftl_update_available")
    assert state.name == "Pi-Hole FTL update available"
    assert state.state == STATE_ON
    assert state.attributes["installed_version"] == "v5.10"
    assert state.attributes["latest_version"] == "v5.11"
    assert (
        state.attributes["release_url"]
        == "https://github.com/pi-hole/FTL/releases/tag/v5.11"
    )

    state = hass.states.get("update.pi_hole_web_update_available")
    assert state.name == "Pi-Hole Web update available"
    assert state.state == STATE_ON
    assert state.attributes["installed_version"] == "v5.7"
    assert state.attributes["latest_version"] == "v5.8"
    assert (
        state.attributes["release_url"]
        == "https://github.com/pi-hole/AdminLTE/releases/tag/v5.8"
    )