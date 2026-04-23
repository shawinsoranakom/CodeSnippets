async def test_init(
    saunabox, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test default state."""

    _, entity_id = saunabox
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-saunaBox-1afe34db9437-thermostat"

    state = hass.states.get(entity_id)
    assert state.name == "My sauna saunaBox-thermostat"

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert supported_features & ClimateEntityFeature.TARGET_TEMPERATURE

    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.OFF]

    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_HVAC_MODE not in state.attributes
    assert ATTR_HVAC_ACTION not in state.attributes

    assert state.attributes[ATTR_MIN_TEMP] == -54.3
    assert state.attributes[ATTR_MAX_TEMP] == 124.3
    assert state.attributes[ATTR_TEMPERATURE] is None
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] is None

    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My sauna"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "saunaBox"
    assert device.sw_version == "1.23"