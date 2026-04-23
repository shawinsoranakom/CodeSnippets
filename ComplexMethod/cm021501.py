async def test_state_init_attribute_variables(
    hass: HomeAssistant,
) -> None:
    """Test a state based template entity initializes icon, name, and picture with variables."""
    source = "switch.foo"
    entity_id = "sensor.foo"

    hass.states.async_set(source, "on", {"friendly_name": "Foo"})
    config = {
        "template": [
            {
                "variables": {
                    "switch": "switch.foo",
                    "on_icon": "mdi:lightbulb",
                    "on_picture": "on.png",
                },
                "sensor": {
                    "variables": {
                        "off_icon": "mdi:lightbulb-off",
                        "off_picture": "off.png",
                    },
                    "name": "{{ state_attr(switch, 'friendly_name') }}",
                    "icon": "{{ on_icon if is_state(switch, 'on') else off_icon }}",
                    "picture": "{{ on_picture if is_state(switch, 'on') else off_picture }}",
                    "state": "{{ is_state(switch, 'on') }}",
                },
            }
        ],
    }
    assert await async_setup_component(
        hass,
        DOMAIN,
        config,
    )
    await hass.async_block_till_done()

    # Check initial state
    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "True"
    assert sensor.attributes["icon"] == "mdi:lightbulb"
    assert sensor.attributes["entity_picture"] == "on.png"
    assert sensor.attributes["friendly_name"] == "Foo"

    hass.states.async_set(source, "off", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    # Check to see that the template light works
    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "False"
    assert sensor.attributes["icon"] == "mdi:lightbulb-off"
    assert sensor.attributes["entity_picture"] == "off.png"
    assert sensor.attributes["friendly_name"] == "Foo"