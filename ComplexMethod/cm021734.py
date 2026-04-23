async def test_setup_all_good_no_recognized_devices(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    client: AqualinkClient,
) -> None:
    """Test setup ending in no devices recognized."""
    config_entry.add_to_hass(hass)

    system = get_aqualink_system(client, cls=IaquaSystem)
    system.online = True
    system.update = AsyncMock()
    systems = {system.serial: system}

    device = get_aqualink_device(system, name="dev_1")
    devices = {device.name: device}

    with (
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.login",
            return_value=None,
        ),
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.get_systems",
            return_value=systems,
        ),
        patch.object(
            system,
            "get_devices",
        ) as mock_get_devices,
    ):
        mock_get_devices.return_value = devices
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert len(hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 0
    assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 0
    assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 0
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 0
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 0

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED