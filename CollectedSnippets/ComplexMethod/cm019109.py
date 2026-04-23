async def test_reconnect(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, config: dict[str, Any]
) -> None:
    """Test that the error and reconnection attempts are logged correctly.

    "Handles device/service unavailable. Log a warning once when
    unavailable, log once when reconnected."

    https://developers.home-assistant.io/docs/en/integration_quality_scale_index.html
    """
    patch_key, entity_id, config_entry = _setup(config)
    config_entry.add_to_hass(hass)

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

    caplog.clear()
    caplog.set_level(logging.WARNING)

    with (
        patchers.patch_connect(False)[patch_key],
        patchers.patch_shell(error=True)[patch_key],
    ):
        for _ in range(5):
            await async_update_entity(hass, entity_id)
            state = hass.states.get(entity_id)
            assert state is not None
            assert state.state == STATE_UNAVAILABLE

    assert len(caplog.record_tuples) == 2
    assert caplog.record_tuples[0][1] == logging.ERROR
    assert caplog.record_tuples[1][1] == logging.WARNING

    caplog.set_level(logging.DEBUG)
    with (
        patchers.patch_connect(True)[patch_key],
        patchers.patch_shell(SHELL_RESPONSE_STANDBY)[patch_key],
        patchers.PATCH_SCREENCAP,
    ):
        await async_update_entity(hass, entity_id)

        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_IDLE
        assert MSG_RECONNECT[patch_key] in caplog.record_tuples[2]