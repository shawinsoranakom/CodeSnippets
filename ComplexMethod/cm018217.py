async def test_get_automation_component_lookup_table_cache(
    hass: HomeAssistant,
) -> None:
    """Test that _get_automation_component_lookup_table caches and rotates properly."""
    triggers: dict[str, dict[str, Any] | None] = {
        "light.turned_on": {"target": {"entity": [{"domain": ["light"]}]}},
        "switch.turned_on": {"target": {"entity": [{"domain": ["switch"]}]}},
    }
    conditions: dict[str, dict[str, Any] | None] = {
        "light.is_on": {"target": {"entity": [{"domain": ["light"]}]}},
        "sensor.is_above": {"target": {"entity": [{"domain": ["sensor"]}]}},
    }
    services: dict[str, dict[str, Any] | None] = {
        "light.turn_on": {"target": {"entity": [{"domain": ["light"]}]}},
        "climate.set_temperature": {"target": {"entity": [{"domain": ["climate"]}]}},
    }

    # First call with triggers - cache should be created with 1 entry
    trigger_result1 = _get_automation_component_lookup_table(hass, "triggers", triggers)
    assert AUTOMATION_COMPONENT_LOOKUP_CACHE in hass.data
    cache = hass.data[AUTOMATION_COMPONENT_LOOKUP_CACHE]
    assert len(cache) == 1

    # Second call with same triggers - should return cached result
    trigger_result2 = _get_automation_component_lookup_table(hass, "triggers", triggers)
    assert trigger_result1 is trigger_result2
    assert len(cache) == 1

    # Call with conditions
    condition_result1 = _get_automation_component_lookup_table(
        hass, "conditions", conditions
    )
    assert condition_result1 is not trigger_result1
    assert len(cache) == 2

    # Call with services
    service_result1 = _get_automation_component_lookup_table(hass, "services", services)
    assert service_result1 is not trigger_result1
    assert service_result1 is not condition_result1
    assert len(cache) == 3

    # Verify all 3 return cached results
    assert (
        _get_automation_component_lookup_table(hass, "triggers", triggers)
        is trigger_result1
    )
    assert (
        _get_automation_component_lookup_table(hass, "conditions", conditions)
        is condition_result1
    )
    assert (
        _get_automation_component_lookup_table(hass, "services", services)
        is service_result1
    )
    assert len(cache) == 3

    # Add a new triggers description dict - replaces previous triggers cache
    new_triggers: dict[str, dict[str, Any] | None] = {
        "fan.turned_on": {"target": {"entity": [{"domain": ["fan"]}]}},
    }
    _get_automation_component_lookup_table(hass, "triggers", new_triggers)
    assert len(cache) == 3

    # Initial trigger cache entry should have been replaced
    trigger_result3 = _get_automation_component_lookup_table(hass, "triggers", triggers)
    assert trigger_result3 is not trigger_result1
    assert len(cache) == 3

    # Verify all 3 return cached results again
    assert (
        _get_automation_component_lookup_table(hass, "triggers", triggers)
        is trigger_result3
    )
    assert (
        _get_automation_component_lookup_table(hass, "conditions", conditions)
        is condition_result1
    )
    assert (
        _get_automation_component_lookup_table(hass, "services", services)
        is service_result1
    )