async def test_update_success(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    entity_id: str,
) -> None:
    """Test turning switch entities on and off."""
    # The entity fixture in conftest.py starts with the switch on and will
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"

    # Turn off the switch and verify the entity state is updated properly with
    # the latest information from the trait.
    assert hass.states.get(entity_id) is not None
    await hass.services.async_call(
        "switch",
        SERVICE_TURN_OFF,
        service_data=None,
        blocking=True,
        target={"entity_id": entity_id},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"

    # Turn back on and verify the entity state is updated properly with the
    # latest information from the trait
    assert hass.states.get(entity_id) is not None
    await hass.services.async_call(
        "switch",
        SERVICE_TURN_ON,
        service_data=None,
        blocking=True,
        target={"entity_id": entity_id},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"