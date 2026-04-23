async def test_light_service_calls_update_entity_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    client: AqualinkClient,
) -> None:
    """Test light service calls update entity state from device properties."""
    config_entry.add_to_hass(hass)

    system = get_aqualink_system(client, cls=IaquaSystem)
    system.online = True
    system.update = AsyncMock()
    systems = {system.serial: system}
    light = get_aqualink_device(
        system, name="aux_1", cls=IaquaLightSwitch, data={"state": "1"}
    )
    devices = {light.name: light}
    system.get_devices = AsyncMock(return_value=devices)

    async def turn_off() -> None:
        light.data["state"] = "0"

    async def turn_on() -> None:
        light.data["state"] = "1"

    light.turn_off = AsyncMock(side_effect=turn_off)
    light.turn_on = AsyncMock(side_effect=turn_on)

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
    entity_id = entity_ids[0]

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON