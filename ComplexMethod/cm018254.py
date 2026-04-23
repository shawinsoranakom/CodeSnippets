async def test_setup_multiple_systems_zones(
    hass: HomeAssistant,
    mock_evolution_client_factory: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a device with multiple systems and zones works."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    mock_evolution_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_FILENAME: "/dev/ttyUSB0", CONF_SYSTEM_ZONE: DEFAULT_SYSTEM_ZONES},
    )
    mock_evolution_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_evolution_entry.entry_id)
    await hass.async_block_till_done()

    # Set the temperature of each zone to its zone number so that we can
    # ensure we've created the right client for each zone.
    for sz, client in mock_evolution_entry.runtime_data.items():
        client.read_current_temperature.return_value = sz[1]
    await trigger_polling(hass, freezer)

    # Check that each system and zone has the expected temperature value to
    # verify that the initial setup flow worked as expected.
    for sz in DEFAULT_SYSTEM_ZONES:
        system = sz[0]
        zone = sz[1]
        state = hass.states.get(f"climate.system_{system}_zone_{zone}")
        assert state, hass.states.async_all()
        assert state.attributes["current_temperature"] == zone

    # Check that the created devices are wired to each other as expected.
    device_registry = dr.async_get(hass)

    def find_device(name):
        return next(filter(lambda x: x.name == name, device_registry.devices.values()))

    sam = find_device("System Access Module")
    s1 = find_device("System 1")
    s2 = find_device("System 2")
    s1z1 = find_device("System 1 Zone 1")
    s1z2 = find_device("System 1 Zone 2")
    s2z3 = find_device("System 2 Zone 3")

    assert sam.via_device_id is None
    assert s1.via_device_id == sam.id
    assert s2.via_device_id == sam.id
    assert s1z1.via_device_id == s1.id
    assert s1z2.via_device_id == s1.id
    assert s2z3.via_device_id == s2.id