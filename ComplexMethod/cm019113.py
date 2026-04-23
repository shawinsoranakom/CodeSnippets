async def test_exception(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Test that the ADB connection gets closed when there is an unforeseen exception.

    HA will attempt to reconnect on the next update.
    """
    patch_key, entity_id, config_entry = _setup(CONFIG_ANDROID_DEFAULT)
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
        caplog.set_level(logging.ERROR)

        # When an unforeseen exception occurs, we close the ADB connection and raise the exception
        with patchers.PATCH_ANDROIDTV_UPDATE_EXCEPTION:
            await async_update_entity(hass, entity_id)

        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_UNAVAILABLE
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples[0][1] == logging.ERROR
        assert caplog.record_tuples[0][2].startswith(
            "Unexpected exception executing an ADB command"
        )

        # On the next update, HA will reconnect to the device
        await async_update_entity(hass, entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_OFF