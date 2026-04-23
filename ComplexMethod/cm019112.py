async def test_update_lock_not_acquired(hass: HomeAssistant) -> None:
    """Test that the state does not get updated when a `LockNotAcquiredException` is raised."""
    patch_key, entity_id, config_entry = _setup(CONFIG_ANDROID_DEFAULT)
    config_entry.add_to_hass(hass)

    with (
        patchers.patch_connect(True)[patch_key],
        patchers.patch_shell(SHELL_RESPONSE_OFF)[patch_key],
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    with patchers.patch_shell(SHELL_RESPONSE_OFF)[patch_key]:
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_OFF

    with (
        patch(
            "androidtv.androidtv.androidtv_async.AndroidTVAsync.update",
            side_effect=LockNotAcquiredException,
        ),
        patchers.patch_shell(SHELL_RESPONSE_STANDBY)[patch_key],
    ):
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_OFF

    with (
        patchers.patch_shell(SHELL_RESPONSE_STANDBY)[patch_key],
        patchers.PATCH_SCREENCAP,
    ):
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_IDLE