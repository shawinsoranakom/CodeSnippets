async def test_sensor_stale_duration(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test turn off on sensor stale."""

    humidifier_switch = "input_boolean.test"
    assert await async_setup_component(
        hass, input_boolean.DOMAIN, {"input_boolean": {"test": None}}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        HUMIDIFIER_DOMAIN,
        {
            "humidifier": {
                "platform": "generic_hygrostat",
                "name": "test",
                "humidifier": humidifier_switch,
                "target_sensor": ENT_SENSOR,
                "initial_state": True,
                "sensor_stale_duration": {"minutes": 10},
            }
        },
    )
    await hass.async_block_till_done()

    _setup_sensor(hass, 23)
    await hass.async_block_till_done()

    assert hass.states.get(humidifier_switch).state == STATE_OFF

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_ENTITY_ID: ENTITY, ATTR_HUMIDITY: 32},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get(humidifier_switch).state == STATE_ON

    # Wait 11 minutes
    freezer.tick(datetime.timedelta(minutes=11))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # 11 minutes later, no news from the sensor : emergency cut off
    assert hass.states.get(humidifier_switch).state == STATE_OFF
    assert "emergency" in caplog.text

    # Updated value from sensor received (same value)
    _setup_sensor(hass, 23)
    await hass.async_block_till_done()

    # A new value has arrived, the humidifier should go ON
    assert hass.states.get(humidifier_switch).state == STATE_ON

    # Wait 11 minutes
    freezer.tick(datetime.timedelta(minutes=11))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # 11 minutes later, no news from the sensor : emergency cut off
    assert hass.states.get(humidifier_switch).state == STATE_OFF
    assert "emergency" in caplog.text

    # Updated value from sensor received (new value)
    _setup_sensor(hass, 24)
    await hass.async_block_till_done()

    # A new value has arrived, the humidifier should go ON
    assert hass.states.get(humidifier_switch).state == STATE_ON

    # Manual turn off
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(humidifier_switch).state == STATE_OFF

    # Wait another 11 minutes
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(minutes=22))
    await hass.async_block_till_done()

    # Still off
    assert hass.states.get(humidifier_switch).state == STATE_OFF

    # Updated value from sensor received
    _setup_sensor(hass, 22)
    await hass.async_block_till_done()

    # Not turning on by itself
    assert hass.states.get(humidifier_switch).state == STATE_OFF