async def test_numerical_state_attribute_crossed_threshold_error_handling(
    hass: HomeAssistant, service_calls: list[ServiceCall]
) -> None:
    """Test numerical state attribute crossed threshold error handling."""

    async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
        return {
            "crossed_threshold": make_entity_numerical_state_crossed_threshold_trigger(
                {"test": DomainSpec(value_source="test_attribute")}
            ),
        }

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.trigger", Mock(async_get_triggers=async_get_triggers))

    hass.states.async_set("test.test_entity", "on", {"test_attribute": 0})

    options = {
        CONF_OPTIONS: {
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.lower"},
                "value_max": {"entity": "sensor.upper"},
            }
        },
    }

    await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    CONF_PLATFORM: "test.crossed_threshold",
                    CONF_TARGET: {CONF_ENTITY_ID: "test.test_entity"},
                }
                | options,
                "action": {
                    "service": "test.automation",
                    "data_template": {CONF_ENTITY_ID: "{{ trigger.entity_id }}"},
                },
            }
        },
    )

    assert len(service_calls) == 0

    # Test the trigger works
    hass.states.async_set("sensor.lower", "10")
    hass.states.async_set("sensor.upper", "90")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    service_calls.clear()

    # Test the trigger does not fire again when still within limits
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 51})
    await hass.async_block_till_done()
    assert len(service_calls) == 0
    service_calls.clear()

    # Test the trigger does not fire when the from-state is unknown or unavailable
    for from_state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        hass.states.async_set("test.test_entity", from_state)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does fire when the attribute value is changing from None
    hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    service_calls.clear()

    # Test the trigger does not fire when the attribute value is outside the limits
    for value in (5, 95):
        hass.states.async_set("test.test_entity", "on", {"test_attribute": value})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does not fire when the attribute value is missing
    hass.states.async_set("test.test_entity", "on", {})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the attribute value is invalid
    for value in ("cat", None):
        hass.states.async_set("test.test_entity", "on", {"test_attribute": value})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Test the trigger does not fire when the lower sensor does not exist
    hass.states.async_remove("sensor.lower")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the lower sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set("sensor.lower", invalid_value)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Reset the lower sensor state to a valid numeric value
    hass.states.async_set("sensor.lower", "10")

    # Test the trigger does not fire when the upper sensor does not exist
    hass.states.async_remove("sensor.upper")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the upper sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set("sensor.upper", invalid_value)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0