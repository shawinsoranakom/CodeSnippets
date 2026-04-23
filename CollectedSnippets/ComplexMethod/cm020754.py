async def test_lock_update_via_pubnub(hass: HomeAssistant) -> None:
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(hass)
    states = hass.states
    assert lock_one.pubsub_channel == "pubsub"
    pubnub = AugustPubNub()

    activities = await _mock_activities_from_fixture(hass, "get_activity.lock.json")
    config_entry, _ = await _create_august_with_devices(
        hass, [lock_one], activities=activities, pubnub=pubnub
    )
    pubnub.connected = True

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKED

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={
                "status": "kAugLockState_Unlocking",
            },
        ),
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=(dt_util.utcnow().timestamp() + 1) * 10000000,
            message={
                "status": "kAugLockState_Locking",
            },
        ),
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert hass.states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    pubnub.connected = True
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    # Ensure pubnub status is always preserved
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=2))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.LOCKING

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=(dt_util.utcnow().timestamp() + 2) * 10000000,
            message={
                "status": "kAugLockState_Unlocking",
            },
        ),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(hours=4))
    await hass.async_block_till_done()
    assert states.get("lock.online_with_doorsense_name").state == LockState.UNLOCKING

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()