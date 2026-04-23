async def test_sensor_actions(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the actions sensor."""
    register_test_entity(
        hass,
        SENSOR_DOMAIN,
        TEST_CAMERA_ID,
        TYPE_MOTIONEYE_ACTION_SENSOR,
        TEST_SENSOR_ACTION_ENTITY_ID,
    )

    client = create_mock_motioneye_client()
    await setup_mock_motioneye_config_entry(hass, client=client)

    entity_state = hass.states.get(TEST_SENSOR_ACTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "3"
    assert entity_state.attributes.get(KEY_ACTIONS) == ["one", "two", "three"]

    updated_camera = copy.deepcopy(TEST_CAMERA)
    updated_camera[KEY_ACTIONS] = ["one"]

    # When the next refresh is called return the updated values.
    client.async_get_cameras = AsyncMock(return_value={"cameras": [updated_camera]})
    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_state = hass.states.get(TEST_SENSOR_ACTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "1"
    assert entity_state.attributes.get(KEY_ACTIONS) == ["one"]

    del updated_camera[KEY_ACTIONS]
    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_state = hass.states.get(TEST_SENSOR_ACTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "0"
    assert entity_state.attributes.get(KEY_ACTIONS) is None