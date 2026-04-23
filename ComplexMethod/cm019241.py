async def test_default_state(hass: HomeAssistant) -> None:
    """Test light switch default state."""
    await async_setup_component(
        hass,
        "light",
        {
            "light": {
                "platform": "switch",
                "entity_id": "switch.test",
                "name": "Christmas Tree Lights",
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.christmas_tree_lights")
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes["supported_features"] == 0
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("color_temp") is None
    assert state.attributes.get("effect_list") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [ColorMode.ONOFF]
    assert state.attributes.get(ATTR_COLOR_MODE) is None