async def test_number_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    controller: EcovacsController,
    tests: list[NumberTestCase],
) -> None:
    """Test that number entity snapshots match."""
    device = controller.devices[0]
    event_bus = device.events

    assert sorted(hass.states.async_entity_ids()) == sorted(
        test.entity_id for test in tests
    )
    for test_case in tests:
        entity_id = test_case.entity_id
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert state.state == STATE_UNKNOWN

        event_bus.notify(test_case.event)
        await block_till_done(hass, event_bus)

        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert snapshot(name=f"{entity_id}:state") == state
        assert state.state == test_case.current_state

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert device_entry.identifiers == {(DOMAIN, device.device_info["did"])}

        device._execute_command.reset_mock()
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: test_case.set_value},
            blocking=True,
        )
        device._execute_command.assert_called_with(test_case.command)