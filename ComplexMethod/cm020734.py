async def test_door_sense_update_via_pubnub(hass: HomeAssistant) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)
    assert lock_one.pubsub_channel == "pubsub"
    pubnub = AugustPubNub()

    activities = await _mock_activities_from_fixture(hass, "get_activity.lock.json")
    config_entry, _ = await _create_august_with_devices(
        hass, [lock_one], activities=activities, pubnub=pubnub
    )
    states = hass.states

    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=_timetoken(),
            message={"status": "kAugLockState_Unlocking", "doorState": "closed"},
        ),
    )

    await hass.async_block_till_done()
    assert (
        states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_OFF
    )

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=_timetoken(),
            message={"status": "kAugLockState_Locking", "doorState": "open"},
        ),
    )
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    pubnub.connected = True
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    # Ensure pubnub status is always preserved
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=2))
    await hass.async_block_till_done()

    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=_timetoken(),
            message={"status": "kAugLockState_Unlocking", "doorState": "open"},
        ),
    )
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=4))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()