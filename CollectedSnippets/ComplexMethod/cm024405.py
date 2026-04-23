async def test_import_config_entry(hass: HomeAssistant) -> None:
    """Test we import config entry and then delete it."""
    entry = MockConfigEntry(
        domain="zone",
        data={
            "name": "from config entry",
            "latitude": 1,
            "longitude": 2,
            "radius": 3,
            "passive": False,
            "icon": "mdi:from-config-entry",
        },
    )
    entry.add_to_hass(hass)
    assert await setup.async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    assert len(hass.config_entries.async_entries()) == 0

    state = hass.states.get("zone.from_config_entry")
    assert state is not None
    assert state.attributes[zone.ATTR_LATITUDE] == 1
    assert state.attributes[zone.ATTR_LONGITUDE] == 2
    assert state.attributes[zone.ATTR_RADIUS] == 3
    assert state.attributes[zone.ATTR_PASSIVE] is False
    assert state.attributes[ATTR_ICON] == "mdi:from-config-entry"