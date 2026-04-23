async def test_sensor_missing_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_envoy: AsyncMock,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test enphase_envoy sensor platform missing data handling."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    ENTITY_BASE = f"{Platform.SENSOR}.envoy_{mock_envoy.serial_number}"

    # force missing data to test 'if == none' code sections
    mock_envoy.data.system_production_phases["L2"] = None
    mock_envoy.data.system_consumption_phases["L2"] = None
    mock_envoy.data.system_net_consumption_phases["L2"] = None
    mock_envoy.data.ctmeter_production = None
    mock_envoy.data.ctmeter_consumption = None
    mock_envoy.data.ctmeter_storage = None
    mock_envoy.data.ctmeter_production_phases = None
    mock_envoy.data.ctmeter_consumption_phases = None
    mock_envoy.data.ctmeter_storage_phases = None
    del mock_envoy.data.ctmeters[CtType.NET_CONSUMPTION]
    del mock_envoy.data.ctmeters_phases[CtType.NET_CONSUMPTION][PhaseNames.PHASE_2]
    del mock_envoy.data.ctmeters[CtType.PRODUCTION]
    del mock_envoy.data.ctmeters_phases[CtType.PRODUCTION][PhaseNames.PHASE_2]
    del mock_envoy.data.ctmeters[CtType.STORAGE]
    del mock_envoy.data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]

    # use different inverter serial to test 'expected inverter missing' code
    mock_envoy.data.inverters["2"] = mock_envoy.data.inverters.pop("1")

    # force HA to detect changed data by changing raw
    mock_envoy.data.raw = {"I": "am changed"}

    # MOve time to next update
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # all these should now be in unknown state
    for entity in (
        "lifetime_energy_production_l2",
        "lifetime_energy_consumption_l2",
        "metering_status_production_ct",
        "metering_status_net_consumption_ct",
        "metering_status_storage_ct",
        "metering_status_production_ct_l2",
        "metering_status_net_consumption_ct_l2",
        "metering_status_storage_ct_l2",
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{entity}"))
        assert entity_state.state == STATE_UNKNOWN

    # test the original inverter is now unknown
    assert (entity_state := hass.states.get("sensor.inverter_1"))
    assert entity_state.state == STATE_UNKNOWN

    del mock_envoy.data.ctmeters_phases[CtType.PRODUCTION]
    del mock_envoy.data.ctmeters_phases[CtType.STORAGE]
    # force HA to detect changed data by changing raw
    mock_envoy.data.raw = {"I": "am changed again"}

    # Move time to next update
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    for entity in (
        "metering_status_production_ct",
        "metering_status_production_ct_l1",
        "metering_status_storage_ct",
        "metering_status_storage_ct_l1",
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{entity}"))
        assert entity_state.state == STATE_UNKNOWN