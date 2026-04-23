async def test_privacy_mode_change_callback(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
) -> None:
    """Test privacy mode changed callback."""

    class callback_mock_class:
        callback_func = None

        def register_callback(
            self, callback_id: str, callback: Callable[[], None], *args, **key_args
        ) -> None:
            if callback_id == "privacy_mode_change":
                self.callback_func = callback

    callback_mock = callback_mock_class()

    reolink_host.model = TEST_HOST_MODEL
    reolink_host.baichuan.events_active = True
    reolink_host.baichuan.subscribe_events.reset_mock(side_effect=True)
    reolink_host.baichuan.register_callback = callback_mock.register_callback
    reolink_host.baichuan.privacy_mode.return_value = True
    reolink_host.audio_record.return_value = True

    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.SWITCH]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = f"{Platform.SWITCH}.{TEST_CAM_NAME}_record_audio"
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    # simulate a TCP push callback signaling a privacy mode change
    reolink_host.baichuan.privacy_mode.return_value = False
    assert callback_mock.callback_func is not None
    callback_mock.callback_func()

    # check that a coordinator update was scheduled.
    reolink_host.get_states.reset_mock()
    assert reolink_host.get_states.call_count == 0

    freezer.tick(5)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert reolink_host.get_states.call_count >= 1
    assert hass.states.get(entity_id).state == STATE_ON

    # test cleanup during unloading, first reset to privacy mode ON
    reolink_host.baichuan.privacy_mode.return_value = True
    callback_mock.callback_func()
    freezer.tick(5)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    # now fire the callback again, but unload before refresh took place
    reolink_host.baichuan.privacy_mode.return_value = False
    callback_mock.callback_func()
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED