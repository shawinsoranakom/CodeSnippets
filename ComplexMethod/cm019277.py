async def test_default_state(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test light group default state."""
    hass.states.async_set("light.kitchen", "on")
    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["light.kitchen", "light.bedroom"],
                "name": "Bedroom Group",
                "unique_id": "unique_identifier",
                "all": "false",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes.get(ATTR_ENTITY_ID) == ["light.kitchen", "light.bedroom"]
    assert state.attributes.get(ATTR_BRIGHTNESS) is None
    assert state.attributes.get(ATTR_HS_COLOR) is None
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) is None
    assert state.attributes.get(ATTR_EFFECT_LIST) is None
    assert state.attributes.get(ATTR_EFFECT) is None

    entry = entity_registry.async_get("light.bedroom_group")
    assert entry
    assert entry.unique_id == "unique_identifier"