async def test_sensor_encharge_power_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_envoy: AsyncMock,
) -> None:
    """Test enphase_envoy encharge_power entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    ENTITY_BASE = f"{Platform.SENSOR}.encharge"

    ENCHARGE_POWER_NAMES = (
        "battery",
        "apparent_power",
        "power",
    )

    ENCHARGE_POWER_TARGETS = [
        (
            sn,
            (
                encharge_power.soc,
                encharge_power.apparent_power_mva / 1000.0,
                encharge_power.real_power_mw / 1000.0,
            ),
        )
        for sn, encharge_power in mock_envoy.data.encharge_power.items()
    ]

    for sn, sn_target in ENCHARGE_POWER_TARGETS:
        for name, target in list(zip(ENCHARGE_POWER_NAMES, sn_target, strict=False)):
            assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{sn}_{name}"))
            assert float(entity_state.state) == target
            assert (
                entity_state.attributes["state_class"] == SensorStateClass.MEASUREMENT
            )

    for sn, encharge_inventory in mock_envoy.data.encharge_inventory.items():
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{sn}_temperature"))
        assert (
            round(
                TemperatureConverter.convert(
                    float(entity_state.state),
                    hass.config.units.temperature_unit,
                    UnitOfTemperature.FAHRENHEIT
                    if encharge_inventory.temperature_unit == "F"
                    else UnitOfTemperature.CELSIUS,
                )
            )
            == encharge_inventory.temperature
        )
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{sn}_last_reported"))
        assert dt_util.parse_datetime(entity_state.state) == dt_util.utc_from_timestamp(
            encharge_inventory.last_report_date
        )
        assert entity_state.attributes.get("state_class") is None