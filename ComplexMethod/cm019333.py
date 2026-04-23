async def test_sensor_aggegated_battery_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_envoy: AsyncMock,
) -> None:
    """Test enphase_envoy aggregated batteries entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.envoy_{sn}"

    data = mock_envoy.data.battery_aggregate
    AGGREGATED_TARGETS: tuple[tuple[Any, ...], ...] = (
        (data.state_of_charge, SensorStateClass.MEASUREMENT),
        (data.available_energy, SensorStateClass.MEASUREMENT),
        (data.max_available_capacity, None),
    )

    for name, target in list(
        zip(AGGREGATED_BATTERY_NAMES, AGGREGATED_TARGETS, strict=False)
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert int(entity_state.state) == target[0]
        assert entity_state.attributes.get("state_class") == target[1]

    data = mock_envoy.data.acb_power
    AGGREGATED_ACB_TARGETS: tuple[int, ...] = (data.charge_wh,)
    for name, target in list(
        zip(AGGREGATED_ACB_BATTERY_NAMES, AGGREGATED_ACB_TARGETS, strict=False)
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert int(entity_state.state) == target
        assert (
            entity_state.attributes.get("state_class") == SensorStateClass.MEASUREMENT
        )