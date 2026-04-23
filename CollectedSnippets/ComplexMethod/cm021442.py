def test_default_setup_params(hass: HomeAssistant) -> None:
    """Test the setup with default parameters."""
    state = hass.states.get(ENTITY_VOLUME)
    assert state.attributes.get(ATTR_MIN) == 0.0
    assert state.attributes.get(ATTR_MAX) == 100.0
    assert state.attributes.get(ATTR_STEP) == 1.0
    assert state.attributes.get(ATTR_MODE) == NumberMode.SLIDER

    state = hass.states.get(ENTITY_PWM)
    assert state.attributes.get(ATTR_MIN) == 0.0
    assert state.attributes.get(ATTR_MAX) == 1.0
    assert state.attributes.get(ATTR_STEP) == 0.01
    assert state.attributes.get(ATTR_MODE) == NumberMode.BOX

    state = hass.states.get(ENTITY_LARGE_RANGE)
    assert state.attributes.get(ATTR_MIN) == 1.0
    assert state.attributes.get(ATTR_MAX) == 1000.0
    assert state.attributes.get(ATTR_STEP) == 1.0
    assert state.attributes.get(ATTR_MODE) == NumberMode.AUTO

    state = hass.states.get(ENTITY_SMALL_RANGE)
    assert state.attributes.get(ATTR_MIN) == 1.0
    assert state.attributes.get(ATTR_MAX) == 255.0
    assert state.attributes.get(ATTR_STEP) == 1.0
    assert state.attributes.get(ATTR_MODE) == NumberMode.AUTO