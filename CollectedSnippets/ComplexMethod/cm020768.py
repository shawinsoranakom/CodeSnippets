async def test_light_set_off(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test set off of the light."""

    entity_id = "light.bedroomlight"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("friendly_name") == "bedroomlight"

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert (
        entry.unique_id
        == "3WRRJR6RCZQZSND8VP0YTO3YXCSOFPKBMW8T51TU-LQ*3-QURR5Q6ADA8ML1TBRG59RRGM1F9LVUZLKPYKFJQHC"
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF