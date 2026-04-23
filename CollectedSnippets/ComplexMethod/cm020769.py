async def test_light_set_brightness(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test set brightness of the light."""

    entity_id = "light.lightbulb"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("friendly_name") == "lightbulb"

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert (
        entry.unique_id
        == "3WRRJR6RCZQZSND8VP0YTO3YXCSOFPKBMW8T51TU-LQ*JHJZIZ9ORJNHB7DZNBNAOSEDECVTTZ48SABTCA3WA3M"
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id], ATTR_BRIGHTNESS: 255},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert int(state.attributes[ATTR_BRIGHTNESS]) == 0