async def test_async_active_zone_with_non_zero_radius(
    hass: HomeAssistant,
) -> None:
    """Test async_active_zone with a non-zero radius."""
    latitude = 32.880600
    longitude = -117.237561

    assert await setup.async_setup_component(
        hass,
        zone.DOMAIN,
        {
            "zone": [
                {
                    "name": "Small Zone",
                    "latitude": 32.980600,
                    "longitude": -117.137561,
                    "radius": 50000,
                },
                {
                    "name": "Big Zone",
                    "latitude": 32.980600,
                    "longitude": -117.137561,
                    "radius": 100000,
                },
            ]
        },
    )

    home_state = hass.states.get("zone.home")
    assert home_state.attributes["radius"] == 100
    assert home_state.attributes["latitude"] == 32.87336
    assert home_state.attributes["longitude"] == -117.22743

    active_zone = zone.async_active_zone(hass, latitude, longitude, 5000)
    assert active_zone.entity_id == "zone.home"
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude, 5000)
    assert active_zone.entity_id == "zone.home"
    assert in_zones == ["zone.home", "zone.small_zone", "zone.big_zone"]

    active_zone = zone.async_active_zone(hass, latitude, longitude, 0)
    assert active_zone.entity_id == "zone.small_zone"
    active_zone, in_zones = zone.async_in_zones(hass, latitude, longitude, 0)
    assert active_zone.entity_id == "zone.small_zone"
    assert in_zones == ["zone.small_zone", "zone.big_zone"]