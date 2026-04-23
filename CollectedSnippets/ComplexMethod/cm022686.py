async def test_camera_with_linked_motion_event(hass: HomeAssistant, run_driver) -> None:
    """Test a camera with a linked motion event entity can update."""
    await async_setup_component(hass, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})
    await async_setup_component(
        hass, camera.DOMAIN, {camera.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    motion_entity_id = "event.motion"

    hass.states.async_set(
        motion_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION},
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
            CONF_LINKED_MOTION_SENSOR: motion_entity_id,
        },
    )
    bridge = HomeBridge("hass", run_driver, "Test Bridge")
    bridge.add_accessory(acc)

    acc.run()

    assert acc.aid == 2
    assert acc.category == 17  # Camera

    service = acc.get_service(SERV_MOTION_SENSOR)
    assert service
    char = service.get_characteristic(CHAR_MOTION_DETECTED)
    assert char

    assert char.value is False
    broker = MagicMock()
    char.broker = broker

    hass.states.async_set(
        motion_entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    assert len(broker.mock_calls) == 0
    broker.reset_mock()
    assert char.value is False

    char.set_value(True)
    fire_time = dt_util.utcnow().isoformat()
    hass.states.async_set(
        motion_entity_id, fire_time, {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    assert len(broker.mock_calls) == 4
    broker.reset_mock()
    assert char.value is False

    hass.states.async_set(
        motion_entity_id,
        fire_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION},
        force_update=True,
    )
    await hass.async_block_till_done()
    assert len(broker.mock_calls) == 0
    broker.reset_mock()

    hass.states.async_set(
        motion_entity_id,
        fire_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION, "other": "attr"},
    )
    await hass.async_block_till_done()
    assert len(broker.mock_calls) == 0
    broker.reset_mock()
    # Ensure we do not throw when the linked
    # motion sensor is removed
    hass.states.async_remove(motion_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert char.value is False

    # Ensure re-adding does not fire an event
    hass.states.async_set(
        motion_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION, "other": "attr"},
    )
    await hass.async_block_till_done()
    assert not broker.mock_calls

    # But a second update does
    broker.reset_mock()
    hass.states.async_set(
        motion_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION},
    )
    await hass.async_block_till_done()
    assert broker.mock_calls

    # Now go unavailable
    broker.reset_mock()
    hass.states.async_set(
        motion_entity_id,
        STATE_UNAVAILABLE,
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION},
    )
    await hass.async_block_till_done()
    assert not broker.mock_calls

    # Going from unavailable to a state should not fire an event
    hass.states.async_set(
        motion_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION},
    )
    await hass.async_block_till_done()
    assert not broker.mock_calls

    # But a another update does
    broker.reset_mock()
    hass.states.async_set(
        motion_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.MOTION, "other": "attr"},
    )
    await hass.async_block_till_done()
    assert broker.mock_calls