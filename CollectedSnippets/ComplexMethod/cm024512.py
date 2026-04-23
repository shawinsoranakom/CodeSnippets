async def test_one_lock_operation_socketio_connected(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test lock and unlock operations are async when socketio is connected."""
    lock_one = await _mock_doorsense_enabled_yale_lock_detail(hass)
    assert lock_one.pubsub_channel == "pubsub"
    states = hass.states

    _, socketio = await _create_yale_with_devices(hass, [lock_one])
    socketio.connected = True

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.LOCKED
    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    await hass.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)

    listener = list(socketio._listeners)[0]
    listener(
        lock_one.device_id,
        dt_util.utcnow() + datetime.timedelta(seconds=1),
        {
            "status": "kAugLockState_Unlocked",
        },
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    lock_state = states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.UNLOCKED
    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    await hass.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)

    listener(
        lock_one.device_id,
        dt_util.utcnow() + datetime.timedelta(seconds=2),
        {
            "status": "kAugLockState_Locked",
        },
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKED

    # No activity means it will be unavailable until the activity feed has data
    assert entity_registry.async_get("sensor.online_with_doorsense_name_operator")
    assert (
        states.get("sensor.online_with_doorsense_name_operator").state == STATE_UNKNOWN
    )

    freezer.tick(INITIAL_LOCK_RESYNC_TIME)

    listener(
        lock_one.device_id,
        dt_util.utcnow() + datetime.timedelta(seconds=2),
        {
            "status": "kAugLockState_Unlocked",
        },
    )

    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKED