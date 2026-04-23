async def test_delay_on(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test binary sensor template delay on."""
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF

    await async_trigger(hass, TEST_ATTRIBUTE_ENTITY_ID, 5)
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_ON

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(TEST_BINARY_SENSOR.entity_id).state == STATE_OFF