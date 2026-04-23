async def test_sensor_ct_phase_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
    cttype: CtType,
) -> None:
    """Test ct phase entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.envoy_{sn}"

    CT_NAMES_FLOAT_PHASE_TARGET = chain(
        *[
            (
                phase_data.energy_delivered / 1000000.0,
                phase_data.energy_received / 1000000.0,
                phase_data.active_power / 1000.0,
                phase_data.frequency,
                phase_data.voltage,
                phase_data.current,
                phase_data.power_factor,
                len(phase_data.status_flags),
            )
            for phase_data in mock_envoy.data.ctmeters_phases[cttype].values()
        ]
    )

    count_names: int = 0
    for name, target in list(
        zip(
            [
                entity.replace("<cttype>", cttype).replace("-", "_")
                for entity in CT_NAMES_FLOAT_PHASE
            ],
            CT_NAMES_FLOAT_PHASE_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert float(entity_state.state) == target
        count_names += 1

    CT_NAMES_STR_PHASE_TARGET = [
        phase_data.metering_status
        for phase_data in mock_envoy.data.ctmeters_phases[cttype].values()
    ]

    for name, target in list(
        zip(
            [
                entity.replace("<cttype>", cttype).replace("-", "_")
                for entity in CT_NAMES_STR_PHASE
            ],
            CT_NAMES_STR_PHASE_TARGET,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert entity_state.state == target
        count_names += 1

    # verify we're testing them all
    assert len(CT_NAMES_FLOAT_PHASE) + len(CT_NAMES_STR_PHASE) == count_names