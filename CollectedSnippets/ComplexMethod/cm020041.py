async def test_zones(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test switch platform with fake data that creates 7 zones with one enabled."""

    zone = hass.states.get("switch.rain_bird_sprinkler_1")
    assert zone is not None
    assert zone.state == "off"
    assert zone.attributes == {
        "friendly_name": "Rain Bird Sprinkler 1",
        "zone": 1,
    }

    zone = hass.states.get("switch.rain_bird_sprinkler_2")
    assert zone is not None
    assert zone.state == "off"
    assert zone.attributes == {
        "friendly_name": "Rain Bird Sprinkler 2",
        "zone": 2,
    }

    zone = hass.states.get("switch.rain_bird_sprinkler_3")
    assert zone is not None
    assert zone.state == "off"

    zone = hass.states.get("switch.rain_bird_sprinkler_4")
    assert zone is not None
    assert zone.state == "off"

    zone = hass.states.get("switch.rain_bird_sprinkler_5")
    assert zone is not None
    assert zone.state == "on"

    zone = hass.states.get("switch.rain_bird_sprinkler_6")
    assert zone is not None
    assert zone.state == "off"

    zone = hass.states.get("switch.rain_bird_sprinkler_7")
    assert zone is not None
    assert zone.state == "off"

    assert not hass.states.get("switch.rain_bird_sprinkler_8")

    # Verify unique id for one of the switches
    entity_entry = entity_registry.async_get("switch.rain_bird_sprinkler_3")
    assert entity_entry.unique_id == "4c:a1:61:00:11:22-3"