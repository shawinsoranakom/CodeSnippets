async def test_door_sense_update_via_socketio(hass: HomeAssistant) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_yale_lock_detail(hass)
    assert lock_one.pubsub_channel == "pubsub"

    activities = await _mock_activities_from_fixture(hass, "get_activity.lock.json")
    config_entry, socketio = await _create_yale_with_devices(
        hass, [lock_one], activities=activities
    )
    states = hass.states
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    listener = list(socketio._listeners)[0]
    listener(
        lock_one.device_id,
        dt_util.utcnow(),
        {"status": "kAugLockState_Unlocking", "doorState": "closed"},
    )

    await hass.async_block_till_done()

    assert (
        states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_OFF
    )

    listener(
        lock_one.device_id,
        dt_util.utcnow(),
        {"status": "kAugLockState_Locking", "doorState": "open"},
    )

    await hass.async_block_till_done()

    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    socketio.connected = True
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    # Ensure socketio status is always preserved
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=2))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    listener(
        lock_one.device_id,
        dt_util.utcnow(),
        {"status": "kAugLockState_Unlocking", "doorState": "open"},
    )

    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=4))
    await hass.async_block_till_done()
    assert states.get("binary_sensor.online_with_doorsense_name_door").state == STATE_ON

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()