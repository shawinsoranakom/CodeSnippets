async def test_set_value(hass: HomeAssistant) -> None:
    """Test set_value method."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {"initial": "test", "min": 3, "max": 10},
                "test_2": {},
            }
        },
    )
    entity_id = "input_text.test_1"
    entity_id_2 = "input_text.test_2"
    assert hass.states.get(entity_id).state == "test"
    assert hass.states.get(entity_id_2).state == "unknown"

    for entity in (entity_id, entity_id_2):
        await async_set_value(hass, entity, "testing")
        assert hass.states.get(entity).state == "testing"

    # Too long for entity 1
    await async_set_value(hass, entity, "testing too long")
    assert hass.states.get(entity_id).state == "testing"

    # Set to empty string
    await async_set_value(hass, entity_id_2, "")
    assert hass.states.get(entity_id_2).state == ""