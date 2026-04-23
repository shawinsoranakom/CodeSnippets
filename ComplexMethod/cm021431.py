async def test_zone_climate_properties(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    zone_device: ZoneDevice,
) -> None:
    """Zone climate exposes expected state attributes."""
    configure_zone_device(
        zone_device,
        zones=[["Living", "1", 22]],
        target_temperature=24,
        mode="cool",
        heating_values="20",
        cooling_values="18",
    )
    await _async_setup_daikin(hass, zone_device)
    entity_id = _zone_entity_id(entity_registry, zone_device, 0)
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_TEMPERATURE] == 18.0
    assert state.attributes[ATTR_MIN_TEMP] == 22.0
    assert state.attributes[ATTR_MAX_TEMP] == 26.0
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.COOL]
    assert state.attributes["zone_id"] == 0