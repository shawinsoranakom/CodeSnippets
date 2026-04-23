async def test_numerical_state_attribute_changed_error_handling(
    hass: HomeAssistant, service_calls: list[ServiceCall]
) -> None:
    """Test numerical state attribute change error handling."""

    async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
        return {
            "attribute_changed": make_entity_numerical_state_changed_trigger(
                {"test": DomainSpec(value_source="test_attribute")}
            ),
        }

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.trigger", Mock(async_get_triggers=async_get_triggers))

    hass.states.async_set("test.test_entity", "on", {"test_attribute": 20})

    options = {
        CONF_OPTIONS: {
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.above"},
                "value_max": {"entity": "sensor.below"},
            }
        }
    }

    await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    CONF_PLATFORM: "test.attribute_changed",
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
    hass.states.async_set("sensor.above", "10")
    hass.states.async_set("sensor.below", "90")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    service_calls.clear()

    # Test the trigger fires again when still within limits
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 51})
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    service_calls.clear()

    # Test the trigger does not fire when the from-state is unknown or unavailable
    for from_state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        hass.states.async_set("test.test_entity", from_state)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

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

    # Test the trigger does not fire when the above sensor does not exist
    hass.states.async_remove("sensor.above")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the above sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set("sensor.above", invalid_value)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0

    # Reset the above sensor state to a valid numeric value
    hass.states.async_set("sensor.above", "10")

    # Test the trigger does not fire when the below sensor does not exist
    hass.states.async_remove("sensor.below")
    hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
    hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    # Test the trigger does not fire when the below sensor state is not numeric
    for invalid_value in ("cat", None):
        hass.states.async_set("sensor.below", invalid_value)
        hass.states.async_set("test.test_entity", "on", {"test_attribute": None})
        hass.states.async_set("test.test_entity", "on", {"test_attribute": 50})
        await hass.async_block_till_done()
        assert len(service_calls) == 0