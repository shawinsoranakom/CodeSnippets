async def test_buttons(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    controller: EcovacsController,
    entities: list[tuple[str, Command]],
) -> None:
    """Test that sensor entity snapshots match."""
    assert hass.states.async_entity_ids() == [e[0] for e in entities]
    device = controller.devices[0]
    for entity_id, command in entities:
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert state.state == STATE_UNKNOWN

        device._execute_command.reset_mock()
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        device._execute_command.assert_called_with(command)

        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert state.state == "2024-01-01T00:00:00+00:00"
        assert snapshot(name=f"{entity_id}:state") == state

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert device_entry.identifiers == {(DOMAIN, device.device_info["did"])}