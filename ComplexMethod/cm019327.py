async def test_sensor_storage_ct_phase_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test storage ct phase entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.envoy_{sn}"

    CT_STORAGE_NAMES_FLOAT_PHASE_TARGET = chain(
        *[
            (
                phase_data.energy_delivered / 1000000.0,
                phase_data.energy_received / 1000000.0,
                phase_data.active_power / 1000.0,
                phase_data.voltage,
                len(phase_data.status_flags),
            )
            for phase_data in mock_envoy.data.ctmeter_storage_phases.values()
        ]
    )

    for name, target in list(
        zip(
            CT_STORAGE_NAMES_FLOAT_PHASE,
            CT_STORAGE_NAMES_FLOAT_PHASE_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert float(entity_state.state) == target

    CT_STORAGE_NAMES_STR_PHASE_TARGET = [
        phase_data.metering_status
        for phase_data in mock_envoy.data.ctmeter_storage_phases.values()
    ]

    for name, target in list(
        zip(
            CT_STORAGE_NAMES_STR_PHASE,
            CT_STORAGE_NAMES_STR_PHASE_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert entity_state.state == target