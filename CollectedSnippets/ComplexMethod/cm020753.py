async def test_one_lock_operation_pubnub_connected(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test lock and unlock operations are async when pubnub is connected."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)
    assert lock_one.pubsub_channel == "pubsub"

    pubnub = AugustPubNub()
    await _create_august_with_devices(hass, [lock_one], pubnub=pubnub)
    pubnub.connected = True

    lock_state = hass.states.get("lock.online_with_doorsense_name")

    assert lock_state.state == LockState.LOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    await hass.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=(dt_util.utcnow().timestamp() + 1) * 10000000,
            message={
                "status": "kAugLockState_Unlocked",
            },
        ),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.UNLOCKED

    assert lock_state.attributes["battery_level"] == 92
    assert lock_state.attributes["friendly_name"] == "online_with_doorsense Name"

    await hass.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=(dt_util.utcnow().timestamp() + 2) * 10000000,
            message={
                "status": "kAugLockState_Locked",
            },
        ),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.LOCKED

    # No activity means it will be unavailable until the activity feed has data
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        hass.states.get("sensor.online_with_doorsense_name_operator").state
        == STATE_UNKNOWN
    )

    freezer.tick(INITIAL_LOCK_RESYNC_TIME)

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=(dt_util.utcnow().timestamp() + 2) * 10000000,
            message={
                "status": "kAugLockState_Unlocked",
            },
        ),
    )
    await hass.async_block_till_done()

    lock_state = hass.states.get("lock.online_with_doorsense_name")
    assert lock_state.state == LockState.UNLOCKED