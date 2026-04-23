async def test_config_options(hass: HomeAssistant) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    test_2_options = ["Good Option", "Better Option", "Best Option"]

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {"options": [1, 2]},
                "test_2": {
                    "name": "Hello World",
                    "icon": "mdi:work",
                    "options": test_2_options,
                    "initial": "Better Option",
                },
            }
        },
    )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")

    assert state_1 is not None
    assert state_2 is not None

    assert state_1.state == "1"
    assert state_1.attributes.get(ATTR_OPTIONS) == ["1", "2"]
    assert ATTR_ICON not in state_1.attributes

    assert state_2.state == "Better Option"
    assert state_2.attributes.get(ATTR_OPTIONS) == test_2_options
    assert state_2.attributes.get(ATTR_FRIENDLY_NAME) == "Hello World"
    assert state_2.attributes.get(ATTR_ICON) == "mdi:work"