async def test_sensor_acb_power_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_envoy: AsyncMock,
) -> None:
    """Test enphase_envoy acb battery power entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.serial_number
    ENTITY_BASE: str = f"{Platform.SENSOR}.acb_{sn}"

    data = mock_envoy.data.acb_power
    ACB_POWER_INT_TARGETS: tuple[int, ...] = (
        data.power,
        data.state_of_charge,
    )
    ACB_POWER_STR_TARGETS: tuple[int, ...] = (data.state,)

    for name, target in list(
        zip(ACB_POWER_INT_NAMES, ACB_POWER_INT_TARGETS, strict=False)
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert int(entity_state.state) == target
        assert entity_state.attributes["state_class"] == SensorStateClass.MEASUREMENT

    for name, target in list(
        zip(ACB_POWER_STR_NAMES, ACB_POWER_STR_TARGETS, strict=False)
    ):
        assert (entity_state := hass.states.get(f"{ENTITY_BASE}_{name}"))
        assert entity_state.state == target
        assert entity_state.attributes.get("state_class") is None