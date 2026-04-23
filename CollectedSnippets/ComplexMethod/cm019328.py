async def test_sensor_ct_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
    cttype: CtType,
) -> None:
    """Test ct entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.envoy_{sn}"

    data = mock_envoy.data.ctmeters[cttype]

    CT_TARGETS_FLOAT = (
        data.energy_delivered / 1000000.0,
        data.energy_received / 1000000.0,
        data.active_power / 1000.0,
        data.frequency,
        data.voltage,
        data.current,
        data.power_factor,
        len(data.status_flags),
    )
    count_names: int = 0

    for name, target in list(
        zip(
            [
                entity.replace("<cttype>", cttype).replace("-", "_")
                for entity in CT_NAMES_FLOAT
            ],
            CT_TARGETS_FLOAT,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert float(entity_state.state) == target
        count_names += 1

    CT_TARGETS_STR = (data.metering_status,)
    for name, target in list(
        zip(
            [
                entity.replace("<cttype>", cttype).replace("-", "_")
                for entity in CT_NAMES_STR
            ],
            CT_TARGETS_STR,
            strict=False,
        )
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert entity_state.state == target
        count_names += 1

    # verify we're testing them all
    assert len(CT_NAMES_FLOAT) + len(CT_NAMES_STR) == count_names