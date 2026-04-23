def test_state_with_unit_and_rounding(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test formatting the state rounded and with unit."""
    entry = entity_registry.async_get_or_create(
        "sensor", "test", "very_unique", suggested_object_id="test"
    )
    entity_registry.async_update_entity_options(
        entry.entity_id,
        "sensor",
        {
            "suggested_display_precision": 2,
        },
    )
    assert entry.entity_id == "sensor.test"

    hass.states.async_set("sensor.test", "23", {ATTR_UNIT_OF_MEASUREMENT: "beers"})
    hass.states.async_set("sensor.test2", "23", {ATTR_UNIT_OF_MEASUREMENT: "beers"})
    hass.states.async_set("sensor.test3", "-0.0", {ATTR_UNIT_OF_MEASUREMENT: "beers"})
    hass.states.async_set("sensor.test4", "-0", {ATTR_UNIT_OF_MEASUREMENT: "beers"})

    # state_with_unit property
    tpl = template.Template("{{ states.sensor.test.state_with_unit }}", hass)
    tpl2 = template.Template("{{ states.sensor.test2.state_with_unit }}", hass)

    # AllStates.__call__ defaults
    tpl3 = template.Template("{{ states('sensor.test') }}", hass)
    tpl4 = template.Template("{{ states('sensor.test2') }}", hass)

    # AllStates.__call__ and with_unit=True
    tpl5 = template.Template("{{ states('sensor.test', with_unit=True) }}", hass)
    tpl6 = template.Template("{{ states('sensor.test2', with_unit=True) }}", hass)

    # AllStates.__call__ and rounded=True
    tpl7 = template.Template("{{ states('sensor.test', rounded=True) }}", hass)
    tpl8 = template.Template("{{ states('sensor.test2', rounded=True) }}", hass)
    tpl9 = template.Template("{{ states('sensor.test3', rounded=True) }}", hass)
    tpl10 = template.Template("{{ states('sensor.test4', rounded=True) }}", hass)

    assert tpl.async_render() == "23.00 beers"
    assert tpl2.async_render() == "23 beers"
    assert tpl3.async_render() == 23
    assert tpl4.async_render() == 23
    assert tpl5.async_render() == "23.00 beers"
    assert tpl6.async_render() == "23 beers"
    assert tpl7.async_render() == 23.0
    assert tpl8.async_render() == 23
    assert tpl9.async_render() == 0.0
    assert tpl10.async_render() == 0

    hass.states.async_set("sensor.test", "23.015", {ATTR_UNIT_OF_MEASUREMENT: "beers"})
    hass.states.async_set("sensor.test2", "23.015", {ATTR_UNIT_OF_MEASUREMENT: "beers"})

    assert tpl.async_render() == "23.02 beers"
    assert tpl2.async_render() == "23.015 beers"
    assert tpl3.async_render() == 23.015
    assert tpl4.async_render() == 23.015
    assert tpl5.async_render() == "23.02 beers"
    assert tpl6.async_render() == "23.015 beers"
    assert tpl7.async_render() == 23.02
    assert tpl8.async_render() == 23.015