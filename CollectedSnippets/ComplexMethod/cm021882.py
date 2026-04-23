def get_and_check_entity_basics(
    hass: HomeAssistant,
    mock_hap: HomematicipHAP,
    entity_id: str,
    entity_name: str,
    device_model: str | None,
) -> tuple[State, HomeMaticIPObject | None]:
    """Get and test basic device."""
    ha_state = hass.states.get(entity_id)
    assert ha_state is not None
    if device_model:
        assert ha_state.attributes[ATTR_MODEL_TYPE] == device_model
    assert ha_state.name == entity_name

    hmip_device = mock_hap.hmip_device_by_entity_id.get(entity_id)

    if hmip_device:
        if isinstance(hmip_device, Device):
            assert ha_state.attributes[ATTR_IS_GROUP] is False
        elif isinstance(hmip_device, Group):
            assert ha_state.attributes[ATTR_IS_GROUP]
    return ha_state, hmip_device