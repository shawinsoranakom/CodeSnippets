async def test_expose_linked_sensors(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test that linked sensors are exposed."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
        },
    )

    humidity_entity_id = "sensor.demo_humidity"
    hass.states.async_set(
        humidity_entity_id,
        50,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        },
    )

    pm25_entity_id = "sensor.demo_pm25"
    hass.states.async_set(
        pm25_entity_id,
        10,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.PM25,
        },
    )

    temperature_entity_id = "sensor.demo_temperature"
    hass.states.async_set(
        temperature_entity_id,
        25,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )

    await hass.async_block_till_done()
    acc = AirPurifier(
        hass,
        hk_driver,
        "Air Purifier",
        entity_id,
        1,
        {
            CONF_LINKED_TEMPERATURE_SENSOR: temperature_entity_id,
            CONF_LINKED_PM25_SENSOR: pm25_entity_id,
            CONF_LINKED_HUMIDITY_SENSOR: humidity_entity_id,
        },
    )
    hk_driver.add_accessory(acc)

    assert acc.linked_humidity_sensor is not None
    assert acc.char_current_humidity is not None
    assert acc.linked_pm25_sensor is not None
    assert acc.char_pm25_density is not None
    assert acc.char_air_quality is not None
    assert acc.linked_temperature_sensor is not None
    assert acc.char_current_temperature is not None

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_current_humidity.value == 50
    assert acc.char_pm25_density.value == 10
    assert acc.char_air_quality.value == 2
    assert acc.char_current_temperature.value == 25

    # Updated humidity should reflect in HomeKit
    broker = MagicMock()
    acc.char_current_humidity.broker = broker
    hass.states.async_set(
        humidity_entity_id,
        60,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidity.value == 60
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    # Change to same state should not trigger update in HomeKit
    hass.states.async_set(
        humidity_entity_id,
        60,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        },
        force_update=True,
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidity.value == 60
    assert len(broker.mock_calls) == 0

    # Updated PM2.5 should reflect in HomeKit
    broker = MagicMock()
    acc.char_pm25_density.broker = broker
    acc.char_air_quality.broker = broker
    hass.states.async_set(
        pm25_entity_id,
        5,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.PM25,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_pm25_density.value == 5
    assert acc.char_air_quality.value == 1
    assert len(broker.mock_calls) == 4
    broker.reset_mock()

    # Change to same state should not trigger update in HomeKit
    hass.states.async_set(
        pm25_entity_id,
        5,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.PM25,
        },
        force_update=True,
    )
    await hass.async_block_till_done()
    assert acc.char_pm25_density.value == 5
    assert acc.char_air_quality.value == 1
    assert len(broker.mock_calls) == 0

    # Updated temperature with different unit should reflect in HomeKit
    broker = MagicMock()
    acc.char_current_temperature.broker = broker
    hass.states.async_set(
        temperature_entity_id,
        60,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_temperature.value == 15.6
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    # Updated temperature should reflect in HomeKit
    broker = MagicMock()
    acc.char_current_temperature.broker = broker
    hass.states.async_set(
        temperature_entity_id,
        30,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_temperature.value == 30
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    # Change to same state should not trigger update in HomeKit
    hass.states.async_set(
        temperature_entity_id,
        30,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
        force_update=True,
    )
    await hass.async_block_till_done()
    assert acc.char_current_temperature.value == 30
    assert len(broker.mock_calls) == 0

    # Should handle unavailable state, show last known value
    hass.states.async_set(
        humidity_entity_id,
        STATE_UNAVAILABLE,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        },
    )
    hass.states.async_set(
        pm25_entity_id,
        STATE_UNAVAILABLE,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.PM25,
        },
    )
    hass.states.async_set(
        temperature_entity_id,
        STATE_UNAVAILABLE,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidity.value == 60
    assert acc.char_pm25_density.value == 5
    assert acc.char_air_quality.value == 1
    assert acc.char_current_temperature.value == 30

    # Check that all goes well if we remove the linked sensors
    hass.states.async_remove(humidity_entity_id)
    hass.states.async_remove(pm25_entity_id)
    hass.states.async_remove(temperature_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert len(acc.char_current_humidity.broker.mock_calls) == 0
    assert len(acc.char_pm25_density.broker.mock_calls) == 0
    assert len(acc.char_air_quality.broker.mock_calls) == 0
    assert len(acc.char_current_temperature.broker.mock_calls) == 0

    # HomeKit will show the last known values
    assert acc.char_current_humidity.value == 60
    assert acc.char_pm25_density.value == 5
    assert acc.char_air_quality.value == 1
    assert acc.char_current_temperature.value == 30