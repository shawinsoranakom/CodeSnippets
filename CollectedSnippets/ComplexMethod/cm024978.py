async def test_numerical_state_attribute_changed_with_unit_error_handling(
    hass: HomeAssistant, service_calls: list[ServiceCall]
) -> None:
    """Test numerical state attribute change with unit conversion error handling."""
    trigger_cls = _make_with_unit_changed_trigger_class()

    async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
        return {"attribute_changed": trigger_cls}

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.trigger", Mock(async_get_triggers=async_get_triggers))

    # Entity reports in °F, trigger configured in °C with above 20°C, below 30°C
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 68,  # 68°F = 20°C
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )

    await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        CONF_PLATFORM: "test.attribute_changed",
                        CONF_TARGET: {CONF_ENTITY_ID: "test.test_entity"},
                        CONF_OPTIONS: {
                            "threshold": {
                                "type": "between",
                                "value_min": {
                                    "number": 20,
                                    "unit_of_measurement": "°C",
                                },
                                "value_max": {
                                    "number": 30,
                                    "unit_of_measurement": "°C",
                                },
                            }
                        },
                    },
                    "action": {
                        "service": "test.numerical_automation",
                        "data_template": {CONF_ENTITY_ID: "{{ trigger.entity_id }}"},
                    },
                },
                {
                    "trigger": {
                        CONF_PLATFORM: "test.attribute_changed",
                        CONF_TARGET: {CONF_ENTITY_ID: "test.test_entity"},
                        CONF_OPTIONS: {
                            "threshold": {
                                "type": "between",
                                "value_min": {"entity": "sensor.above"},
                                "value_max": {"entity": "sensor.below"},
                            }
                        },
                    },
                    "action": {
                        "service": "test.entity_automation",
                        "data_template": {CONF_ENTITY_ID: "{{ trigger.entity_id }}"},
                    },
                },
            ]
        },
    )

    assert len(service_calls) == 0

    # 77°F = 25°C, within range (above 20, below 30) - should trigger numerical
    # Entity automation won't trigger because sensor.above/below don't exist yet
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 77,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].service == "numerical_automation"
    service_calls.clear()

    # 59°F = 15°C, below 20°C - should NOT trigger
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 59,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # 95°F = 35°C, above 30°C - should NOT trigger
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 95,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Set up entity limits referencing sensors that report in °F
    hass.states.async_set(
        "sensor.above",
        "68",  # 68°F = 20°C
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    hass.states.async_set(
        "sensor.below",
        "86",  # 86°F = 30°C
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )

    # 77°F = 25°C, between 20°C and 30°C - should trigger both automations
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 77,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert {call.service for call in service_calls} == {
        "numerical_automation",
        "entity_automation",
    }
    service_calls.clear()

    # Test the trigger does not fire when the attribute value is missing
    hass.states.async_set("test.test_entity", "on", {})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the attribute value is invalid
    for value in ("cat", None):
        hass.states.async_set(
            "test.test_entity",
            "on",
            {
                "test_attribute": value,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
            },
        )
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does not fire when the unit is incompatible
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": 50,
            ATTR_UNIT_OF_MEASUREMENT: "invalid_unit",
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the above sensor does not exist
    hass.states.async_remove("sensor.above")
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": None,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {"test_attribute": 50, ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the above sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set(
            "sensor.above",
            invalid_value,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
        )
        hass.states.async_set(
            "test.test_entity",
            "on",
            {
                "test_attribute": None,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
            },
        )
        hass.states.async_set(
            "test.test_entity",
            "on",
            {
                "test_attribute": 50,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
            },
        )
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does not fire when the above sensor's unit is incompatible
    hass.states.async_set(
        "sensor.above",
        "68",  # 68°F = 20°C
        {ATTR_UNIT_OF_MEASUREMENT: "invalid_unit"},
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": None,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {"test_attribute": 50, ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Reset the above sensor state to a valid numeric value
    hass.states.async_set(
        "sensor.above",
        "68",  # 68°F = 20°C
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )

    # Test the trigger does not fire when the below sensor does not exist
    hass.states.async_remove("sensor.below")
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": None,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {"test_attribute": 50, ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the below sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set("sensor.below", invalid_value)
        hass.states.async_set(
            "test.test_entity",
            "on",
            {
                "test_attribute": None,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
            },
        )
        hass.states.async_set(
            "test.test_entity",
            "on",
            {
                "test_attribute": 50,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
            },
        )
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does not fire when the below sensor's unit is incompatible
    hass.states.async_set(
        "sensor.below",
        "68",  # 68°F = 20°C
        {ATTR_UNIT_OF_MEASUREMENT: "invalid_unit"},
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {
            "test_attribute": None,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT,
        },
    )
    hass.states.async_set(
        "test.test_entity",
        "on",
        {"test_attribute": 50, ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0