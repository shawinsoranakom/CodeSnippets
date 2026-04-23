async def test_camera_wake_callback(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
) -> None:
    """Test camera wake callback."""

    class callback_mock_class:
        callback_func = None

        def register_callback(
            self, callback_id: str, callback: Callable[[], None], *args, **key_args
        ) -> None:
            if callback_id == "camera_0_wake":
                self.callback_func = callback

    callback_mock = callback_mock_class()

    reolink_host.model = TEST_HOST_MODEL
    reolink_host.baichuan.events_active = True
    reolink_host.baichuan.subscribe_events.reset_mock(side_effect=True)
    reolink_host.baichuan.register_callback = callback_mock.register_callback
    reolink_host.sleeping.return_value = True
    reolink_host.audio_record.return_value = True

    with (
        patch("homeassistant.components.reolink.PLATFORMS", [Platform.SWITCH]),
        patch(
            "homeassistant.components.reolink.host.time",
            return_value=BATTERY_ALL_WAKE_UPDATE_INTERVAL,
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = f"{Platform.SWITCH}.{TEST_CAM_NAME}_record_audio"
    assert hass.states.get(entity_id).state == STATE_ON

    reolink_host.sleeping.return_value = False
    reolink_host.get_states.reset_mock()
    assert reolink_host.get_states.call_count == 0

    # simulate a TCP push callback signaling the battery camera woke up
    reolink_host.audio_record.return_value = False
    assert callback_mock.callback_func is not None
    with (
        patch(
            "homeassistant.components.reolink.host.time",
            return_value=BATTERY_ALL_WAKE_UPDATE_INTERVAL
            + BATTERY_PASSIVE_WAKE_UPDATE_INTERVAL
            + 5,
        ),
        patch(
            "homeassistant.components.reolink.time",
            return_value=BATTERY_ALL_WAKE_UPDATE_INTERVAL
            + BATTERY_PASSIVE_WAKE_UPDATE_INTERVAL
            + 5,
        ),
    ):
        callback_mock.callback_func()
        await hass.async_block_till_done()

    # check that a coordinator update was scheduled.
    assert reolink_host.get_states.call_count >= 1
    assert hass.states.get(entity_id).state == STATE_OFF