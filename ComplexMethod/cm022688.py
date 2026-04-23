async def test_camera_with_linked_doorbell_event(
    hass: HomeAssistant, run_driver
) -> None:
    """Test a camera with a linked doorbell event can update."""
    await async_setup_component(hass, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
        hass, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    doorbell_entity_id = "event.doorbell"

    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    entity_id = "camera.demo_camera"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Camera(
        hass,
        run_driver,
        "Camera",
        entity_id,
        2,
        {
            CONF_STREAM_SOURCE: "/dev/null",
            CONF_SUPPORT_AUDIO: True,
            CONF_VIDEO_CODEC: VIDEO_CODEC_H264_OMX,
            CONF_AUDIO_CODEC: AUDIO_CODEC_COPY,
            CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id,
        },
    )
    bridge = HomeBridge("hass", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    service = acc.get_service(SERV_DOORBELL)
    assert service
    char = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    assert char

    assert char.value is None

    service2 = acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH)
    assert service2
    char2 = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    assert char2
    broker = MagicMock()
    char2.broker = broker
    assert char2.value is None

    hass.states.async_set(
        doorbell_entity_id,
        STATE_UNKNOWN,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    assert char.value is None
    assert char2.value is None
    assert len(broker.mock_calls) == 0

    char.set_value(True)
    char2.set_value(True)
    broker.reset_mock()

    original_time = dt_util.utcnow().isoformat()
    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    assert char.value is None
    assert char2.value is None
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
        force_update=True,
    )
    await hass.async_block_till_done()
    assert char.value is None
    assert char2.value is None
    assert len(broker.mock_calls) == 0
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL, "other": "attr"},
    )
    await hass.async_block_till_done()
    assert char.value is None
    assert char2.value is None
    assert len(broker.mock_calls) == 0
    broker.reset_mock()

    # Ensure we do not throw when the linked
    # doorbell sensor is removed
    hass.states.async_remove(doorbell_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert char.value is None
    assert char2.value is None

    await hass.async_block_till_done()
    hass.states.async_set(
        doorbell_entity_id,
        STATE_UNAVAILABLE,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    # Ensure re-adding does not fire an event
    assert not broker.mock_calls
    broker.reset_mock()

    # going from unavailable to a state should not fire an event
    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    assert not broker.mock_calls

    # But a second update does
    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    assert broker.mock_calls