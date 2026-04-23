async def test_switch_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    controller: EcovacsController,
    tests: list[SwitchTestCase],
) -> None:
    """Test switch entities."""
    device = controller.devices[0]
    event_bus = device.events

    assert hass.states.async_entity_ids() == [test.entity_id for test in tests]
    for test_case in tests:
        entity_id = test_case.entity_id
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert state.state == STATE_OFF

        event_bus.notify(test_case.event)
        await block_till_done(hass, event_bus)

        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert snapshot(name=f"{entity_id}:state") == state
        assert state.state == STATE_ON

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert device_entry.identifiers == {(DOMAIN, device.device_info["did"])}

        device._execute_command.reset_mock()
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        device._execute_command.assert_called_with(test_case.command(False))

        device._execute_command.reset_mock()
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        device._execute_command.assert_called_with(test_case.command(True))