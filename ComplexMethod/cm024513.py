async def test_lock_update_via_socketio(hass: HomeAssistant) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_yale_lock_detail(hass)
    assert lock_one.pubsub_channel == "pubsub"

    activities = await _mock_activities_from_fixture(hass, "get_activity.lock.json")
    config_entry, socketio = await _create_yale_with_devices(
        hass, [lock_one], activities=activities
    )
    socketio.connected = True
    states = hass.states

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKED

    listener = list(socketio._listeners)[0]
    listener(
        lock_one.device_id,
        dt_util.utcnow(),
        {
            "status": "kAugLockState_Unlocking",
        },
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    listener(
        lock_one.device_id,
        dt_util.utcnow(),
        {
            "status": "kAugLockState_Locking",
        },
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    socketio.connected = True
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    # Ensure socketio status is always preserved
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=2))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    listener(
        lock_one.device_id,
        dt_util.utcnow() + datetime.timedelta(seconds=2),
        {
            "status": "kAugLockState_Unlocking",
        },
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=4))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()