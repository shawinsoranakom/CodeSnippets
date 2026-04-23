async def test_doorbell_update_via_pubnub(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test creation of a doorbell that can be updated via pubnub."""
    doorbell_one = await _mock_doorbell_from_fixture(hass, "get_doorbell.json")
    pubnub = AugustPubNub()

    await _create_august_with_devices(hass, [doorbell_one], pubnub=pubnub)
    assert doorbell_one.pubsub_channel == "7c7a6672-59c8-3333-ffff-dcd98705cccc"

    motion_state = hass.states.get("event.k98gidt45gul_name_motion")
    assert motion_state is not None
    assert motion_state.state == STATE_UNKNOWN
    doorbell_state = hass.states.get("event.k98gidt45gul_name_doorbell")
    assert doorbell_state is not None
    assert doorbell_state.state == STATE_UNKNOWN

    pubnub.message(
        pubnub,
        Mock(
            channel=doorbell_one.pubsub_channel,
            timetoken=_timetoken(),
            message={
                "status": "doorbell_motion_detected",
                "data": {
                    "event": "doorbell_motion_detected",
                    "image": {
                        "height": 640,
                        "width": 480,
                        "format": "jpg",
                        "created_at": "2021-03-16T02:36:26.886Z",
                        "bytes": 14061,
                        "secure_url": (
                            "https://dyu7azbnaoi74.cloudfront.net/images/1f8.jpeg"
                        ),
                        "url": "https://dyu7azbnaoi74.cloudfront.net/images/1f8.jpeg",
                        "etag": "09e839331c4ea59eef28081f2caa0e90",
                    },
                    "doorbellName": "Front Door",
                    "callID": None,
                    "origin": "mars-api",
                    "mutableContent": True,
                },
            },
        ),
    )

    await hass.async_block_till_done()

    motion_state = hass.states.get("event.k98gidt45gul_name_motion")
    assert motion_state is not None
    assert motion_state.state != STATE_UNKNOWN
    isotime = motion_state.state

    freezer.tick(40)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    motion_state = hass.states.get("event.k98gidt45gul_name_motion")
    assert motion_state is not None
    assert motion_state.state != STATE_UNKNOWN

    pubnub.message(
        pubnub,
        Mock(
            channel=doorbell_one.pubsub_channel,
            timetoken=_timetoken(),
            message={
                "status": "buttonpush",
            },
        ),
    )
    await hass.async_block_till_done()

    doorbell_state = hass.states.get("event.k98gidt45gul_name_doorbell")
    assert doorbell_state is not None
    assert doorbell_state.state != STATE_UNKNOWN
    isotime = motion_state.state

    freezer.tick(40)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    doorbell_state = hass.states.get("event.k98gidt45gul_name_doorbell")
    assert doorbell_state is not None
    assert doorbell_state.state != STATE_UNKNOWN
    assert motion_state.state == isotime