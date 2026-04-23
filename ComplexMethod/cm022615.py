async def test_switch_turn_on_off(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test turning the switch on and off."""
    client = create_mock_motioneye_client()
    await setup_mock_motioneye_config_entry(hass, client=client)

    # Verify switch is on.
    entity_state = hass.states.get(TEST_SWITCH_MOTION_DETECTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "on"

    client.async_get_camera = AsyncMock(return_value=TEST_CAMERA)

    expected_camera = copy.deepcopy(TEST_CAMERA)
    expected_camera[KEY_MOTION_DETECTION] = False

    # When the next refresh is called return the updated values.
    client.async_get_cameras = AsyncMock(return_value={"cameras": [expected_camera]})

    # Turn switch off.
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH_MOTION_DETECTION_ENTITY_ID},
        blocking=True,
    )

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify correct parameters are passed to the library.
    assert client.async_set_camera.call_args == call(TEST_CAMERA_ID, expected_camera)

    # Verify the switch turns off.
    entity_state = hass.states.get(TEST_SWITCH_MOTION_DETECTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "off"

    # When the next refresh is called return the updated values.
    client.async_get_cameras = AsyncMock(return_value={"cameras": [TEST_CAMERA]})

    # Turn switch on.
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH_MOTION_DETECTION_ENTITY_ID},
        blocking=True,
    )

    # Verify correct parameters are passed to the library.
    assert client.async_set_camera.call_args == call(TEST_CAMERA_ID, TEST_CAMERA)

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify the switch turns on.
    entity_state = hass.states.get(TEST_SWITCH_MOTION_DETECTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "on"