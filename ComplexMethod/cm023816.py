async def test_bpup_goes_offline_and_recovers_same_entity(hass: HomeAssistant) -> None:
    """Test that push updates fail and we fallback to polling and then bpup recovers.

    The BPUP recovery is triggered by an update for the entity and
    we do not fallback to polling because state is in sync.
    """
    bpup_subs = BPUPSubscriptions()
    with patch(
        "homeassistant.components.bond.BPUPSubscriptions",
        return_value=bpup_subs,
    ):
        await setup_platform(
            hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
        )

    bpup_subs.notify(
        {
            "s": 200,
            "t": "devices/test-device-id/state",
            "b": {"power": 1, "speed": 3, "direction": 0},
        }
    )
    await hass.async_block_till_done()
    assert hass.states.get("fan.name_1").attributes[fan.ATTR_PERCENTAGE] == 100

    # Send a message for the wrong device to make sure its ignored
    # we should never get this callback
    bpup_subs.notify(
        {
            "s": 200,
            "t": "devices/other-device-id/state",
            "b": {"power": 1, "speed": 1, "direction": 0},
        }
    )
    await hass.async_block_till_done()
    assert hass.states.get("fan.name_1").attributes[fan.ATTR_PERCENTAGE] == 100

    # Test we ignore messages for the wrong topic
    bpup_subs.notify(
        {
            "s": 200,
            "t": "devices/test-device-id/other_topic",
            "b": {"power": 1, "speed": 1, "direction": 0},
        }
    )
    await hass.async_block_till_done()
    assert hass.states.get("fan.name_1").attributes[fan.ATTR_PERCENTAGE] == 100

    bpup_subs.notify(
        {
            "s": 200,
            "t": "devices/test-device-id/state",
            "b": {"power": 1, "speed": 1, "direction": 0},
        }
    )
    await hass.async_block_till_done()
    assert hass.states.get("fan.name_1").attributes[fan.ATTR_PERCENTAGE] == 33

    bpup_subs.last_message_time = -BPUP_ALIVE_TIMEOUT
    with patch_bond_device_state(side_effect=TimeoutError):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=230))
        await hass.async_block_till_done()

    assert hass.states.get("fan.name_1").state == STATE_UNAVAILABLE

    # Ensure we do not poll to get the state
    # since bpup has recovered and we know we
    # are back in sync
    with patch_bond_device_state(side_effect=Exception):
        bpup_subs.notify(
            {
                "s": 200,
                "t": "devices/test-device-id/state",
                "b": {"power": 1, "speed": 2, "direction": 0},
            }
        )
        await hass.async_block_till_done()

    state = hass.states.get("fan.name_1")
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66