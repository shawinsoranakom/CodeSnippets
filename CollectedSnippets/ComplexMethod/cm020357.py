async def test_update_no_versions(hass: HomeAssistant) -> None:
    """Tests update entity when no version data available."""
    mocked_hole = _create_mocked_hole(has_versions=False, api_version=6)
    entry = MockConfigEntry(domain=pi_hole.DOMAIN, data=CONFIG_DATA_DEFAULTS)
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole):
        assert await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()

    state = hass.states.get("update.pi_hole_core_update_available")
    assert state.name == "Pi-Hole Core update available"
    assert state.state == STATE_UNKNOWN
    assert state.attributes["installed_version"] is None
    assert state.attributes["latest_version"] is None
    assert state.attributes["release_url"] is None

    state = hass.states.get("update.pi_hole_ftl_update_available")
    assert state.name == "Pi-Hole FTL update available"
    assert state.state == STATE_UNKNOWN
    assert state.attributes["installed_version"] is None
    assert state.attributes["latest_version"] is None
    assert state.attributes["release_url"] is None

    state = hass.states.get("update.pi_hole_web_update_available")
    assert state.name == "Pi-Hole Web update available"
    assert state.state == STATE_UNKNOWN
    assert state.attributes["installed_version"] is None
    assert state.attributes["latest_version"] is None
    assert state.attributes["release_url"] is None