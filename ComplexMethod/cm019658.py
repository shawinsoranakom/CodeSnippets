async def test_gen24_storage(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test Fronius Gen24 inverter with BYD battery and Ohmpilot entities."""

    def assert_state(entity_id, expected_state):
        state = hass.states.get(entity_id)
        assert state
        assert state.state == str(expected_state)

    mock_responses(aioclient_mock, fixture_set="gen24_storage")
    config_entry = await setup_fronius_integration(
        hass, is_logger=False, unique_id="12345678"
    )

    assert len(hass.states.async_all(domain_filter=SENSOR_DOMAIN)) == 73
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)

    # Devices
    solar_net = device_registry.async_get_device(
        identifiers={(DOMAIN, "solar_net_12345678")}
    )
    assert solar_net.configuration_url == "http://fronius"
    assert solar_net.manufacturer == "Fronius"
    assert solar_net.name == "SolarNet"

    inverter_1 = device_registry.async_get_device(identifiers={(DOMAIN, "12345678")})
    assert inverter_1.manufacturer == "Fronius"
    assert inverter_1.model == "Gen24"
    assert inverter_1.name == "Gen24 Storage"

    meter = device_registry.async_get_device(identifiers={(DOMAIN, "1234567890")})
    assert meter.manufacturer == "Fronius"
    assert meter.model == "Smart Meter TS 65A-3"
    assert meter.name == "Smart Meter TS 65A-3"

    ohmpilot = device_registry.async_get_device(identifiers={(DOMAIN, "23456789")})
    assert ohmpilot.manufacturer == "Fronius"
    assert ohmpilot.model == "Ohmpilot 6"
    assert ohmpilot.name == "Ohmpilot"
    assert ohmpilot.sw_version == "1.0.25-3"

    storage = device_registry.async_get_device(
        identifiers={(DOMAIN, "P030T020Z2001234567     ")}
    )
    assert storage.manufacturer == "BYD"
    assert storage.model == "BYD Battery-Box Premium HV"
    assert storage.name == "BYD Battery-Box Premium HV"