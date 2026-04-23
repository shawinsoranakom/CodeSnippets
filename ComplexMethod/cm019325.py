async def test_sensor_production_ct_phase_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test production ct phase entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.envoy_{sn}"

    CT_PRODUCTION_NAMES_FLOAT_TARGET = [
        len(phase_data.status_flags)
        for phase_data in mock_envoy.data.ctmeter_production_phases.values()
    ]

    for name, target in list(
        zip(
            CT_PRODUCTION_NAMES_FLOAT_PHASE,
            CT_PRODUCTION_NAMES_FLOAT_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert float(entity_state.state) == target

    CT_PRODUCTION_NAMES_STR_TARGET = [
        phase_data.metering_status
        for phase_data in mock_envoy.data.ctmeter_production_phases.values()
    ]

    for name, target in list(
        zip(
            CT_PRODUCTION_NAMES_STR_PHASE,
            CT_PRODUCTION_NAMES_STR_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert entity_state.state == target