async def test_primo_s0(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test Fronius Primo dual inverter with S0 meter entities."""

    def assert_state(entity_id, expected_state):
        state = hass.states.get(entity_id)
        assert state
        assert state.state == str(expected_state)

    mock_responses(aioclient_mock, fixture_set="primo_s0", inverter_ids=[1, 2])
    config_entry = await setup_fronius_integration(hass, is_logger=True)

    assert len(hass.states.async_all(domain_filter=SENSOR_DOMAIN)) == 49
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)

    # Devices
    solar_net = device_registry.async_get_device(
        identifiers={(DOMAIN, "solar_net_123.4567890")}
    )
    assert solar_net.configuration_url == "http://fronius"
    assert solar_net.manufacturer == "Fronius"
    assert solar_net.model == "fronius-datamanager-card"
    assert solar_net.name == "SolarNet"
    assert solar_net.sw_version == "3.18.7-1"

    inverter_1 = device_registry.async_get_device(identifiers={(DOMAIN, "123456")})
    assert inverter_1.manufacturer == "Fronius"
    assert inverter_1.model == "Primo 5.0-1"
    assert inverter_1.name == "Primo 5.0-1"

    inverter_2 = device_registry.async_get_device(identifiers={(DOMAIN, "234567")})
    assert inverter_2.manufacturer == "Fronius"
    assert inverter_2.model == "Primo 3.0-1"
    assert inverter_2.name == "Primo 3.0-1"

    meter = device_registry.async_get_device(
        identifiers={(DOMAIN, "solar_net_123.4567890:S0 Meter at inverter 1")}
    )
    assert meter.manufacturer == "Fronius"
    assert meter.model == "S0 Meter at inverter 1"
    assert meter.name == "S0 Meter at inverter 1"