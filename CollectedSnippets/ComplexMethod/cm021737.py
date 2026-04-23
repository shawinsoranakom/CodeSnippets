async def test_entity_assumed_and_available(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    client: AqualinkClient,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test assumed_state and_available properties for all values of online."""
    config_entry.add_to_hass(hass)

    system = get_aqualink_system(client, cls=IaquaSystem)
    system.online = True
    systems = {system.serial: system}

    light = get_aqualink_device(
        system, name="aux_1", cls=IaquaLightSwitch, data={"state": "1"}
    )
    devices = {light.name: light}
    system.get_devices = AsyncMock(return_value=devices)
    system.update = AsyncMock()

    with (
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.login",
            return_value=None,
        ),
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.get_systems",
            return_value=systems,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entity_ids = hass.states.async_entity_ids(LIGHT_DOMAIN)
    assert len(entity_ids) == 1

    name = entity_ids[0]

    # None means maybe.
    light.system.online = None
    await _advance_coordinator_time(hass, freezer)
    state = hass.states.get(name)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get(ATTR_ASSUMED_STATE) is True

    light.system.online = False
    await _advance_coordinator_time(hass, freezer)
    state = hass.states.get(name)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get(ATTR_ASSUMED_STATE) is True

    light.system.online = True
    await _advance_coordinator_time(hass, freezer)
    state = hass.states.get(name)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE) is None