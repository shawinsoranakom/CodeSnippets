async def test_setup_all_good_all_device_types(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    client: AqualinkClient,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test setup ending in one device of each type recognized."""
    config_entry.add_to_hass(hass)

    system = get_aqualink_system(client, cls=IaquaSystem)
    system.online = True
    system.update = AsyncMock()
    systems = {system.serial: system}

    devices = [
        get_aqualink_device(
            system, name="aux_1", cls=IaquaAuxSwitch, data={"state": "0"}
        ),
        get_aqualink_device(
            system, name="freeze_protection", cls=IaquaBinarySensor, data={"state": "0"}
        ),
        get_aqualink_device(
            system, name="aux_2", cls=IaquaLightSwitch, data={"state": "0"}
        ),
        get_aqualink_device(system, name="ph", cls=IaquaSensor, data={"state": "7.2"}),
        get_aqualink_device(
            system, name="pool_set_point", cls=IaquaThermostat, data={"state": "0"}
        ),
    ]
    devices = {d.name: d for d in devices}

    pool_heater = get_aqualink_device(
        system, name="pool_heater", cls=IaquaAuxSwitch, data={"state": "0"}
    )
    pool_temp = get_aqualink_device(
        system, name="pool_temp", cls=IaquaSensor, data={"state": "72"}
    )
    system.devices = {
        **{d.name: d for d in devices.values()},
        pool_heater.name: pool_heater,
        pool_temp.name: pool_temp,
    }

    system.get_devices = AsyncMock(return_value=devices)

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

    assert config_entry.state is ConfigEntryState.LOADED

    assert len(hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    for domain in (
        BINARY_SENSOR_DOMAIN,
        CLIMATE_DOMAIN,
        LIGHT_DOMAIN,
        SENSOR_DOMAIN,
        SWITCH_DOMAIN,
    ):
        for entity_id in hass.states.async_entity_ids(domain):
            entry = entity_registry.async_get(entity_id)
            assert entry is not None
            assert entry.has_entity_name is True

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED