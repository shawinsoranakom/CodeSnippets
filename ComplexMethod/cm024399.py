async def test_setup(hass: HomeAssistant) -> None:
    """Test a successful setup."""
    info = {
        "name": "Test Zone",
        "latitude": 32.880837,
        "longitude": -117.237561,
        "radius": 250,
        "passive": True,
    }
    assert await setup.async_setup_component(hass, zone.DOMAIN, {"zone": info})

    assert len(hass.states.async_entity_ids("zone")) == 2
    state = hass.states.get("zone.test_zone")
    assert info["name"] == state.name
    assert info["latitude"] == state.attributes["latitude"]
    assert info["longitude"] == state.attributes["longitude"]
    assert info["radius"] == state.attributes["radius"]
    assert info["passive"] == state.attributes["passive"]