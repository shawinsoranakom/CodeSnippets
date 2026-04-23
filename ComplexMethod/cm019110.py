async def test_sources(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Test that sources (i.e., apps) are handled correctly for Android and Fire TV devices."""
    conf_apps = {
        "com.app.test1": "TEST 1",
        "com.app.test3": None,
        "com.app.test4": SHELL_RESPONSE_OFF,
    }
    patch_key, entity_id, config_entry = _setup(config)
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_APPS: conf_apps})

    with (
        patchers.patch_connect(True)[patch_key],
        patchers.patch_shell(SHELL_RESPONSE_OFF)[patch_key],
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_OFF

    patch_update = patchers.patch_androidtv_update(
        "playing",
        "com.app.test1",
        ["com.app.test1", "com.app.test2", "com.app.test3", "com.app.test4"],
        "hdmi",
        False,
        1,
        "HW5",
    )

    with patch_update[config[DOMAIN][CONF_DEVICE_CLASS]]:
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_PLAYING
        assert state.attributes["source"] == "TEST 1"
        assert sorted(state.attributes["source_list"]) == ["TEST 1", "com.app.test2"]

    patch_update = patchers.patch_androidtv_update(
        "playing",
        "com.app.test2",
        ["com.app.test2", "com.app.test1", "com.app.test3", "com.app.test4"],
        "hdmi",
        True,
        0,
        "HW5",
    )

    with patch_update[config[DOMAIN][CONF_DEVICE_CLASS]]:
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_PLAYING
        assert state.attributes["source"] == "com.app.test2"
        assert sorted(state.attributes["source_list"]) == ["TEST 1", "com.app.test2"]