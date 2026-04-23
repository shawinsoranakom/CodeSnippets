async def test_cover_state_updates(
    hass: HomeAssistant,
    setup_overkiz_integration: SetupOverkizIntegration,
    mock_client: MockOverkizClient,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test cover state updates via events and execution tracking."""
    await setup_overkiz_integration(fixture=SHUTTER.fixture)

    assert hass.states.get(SHUTTER.entity_id).attributes[ATTR_CURRENT_POSITION] == 0

    # Position update via device state change event
    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.DEVICE_STATE_CHANGED.value,
                device_url=SHUTTER.device_url,
                device_states=[
                    {
                        "name": OverkizState.CORE_CLOSURE.value,
                        "type": 1,
                        "value": 0,
                    },
                    {
                        "name": OverkizState.CORE_TARGET_CLOSURE.value,
                        "type": 1,
                        "value": 0,
                    },
                    {
                        "name": OverkizState.CORE_MOVING.value,
                        "type": 6,
                        "value": False,
                    },
                    {
                        "name": OverkizState.CORE_OPEN_CLOSED.value,
                        "type": 3,
                        "value": OverkizCommandParam.OPEN.value,
                    },
                ],
            )
        ],
    )

    state = hass.states.get(SHUTTER.entity_id)
    assert state.attributes[ATTR_CURRENT_POSITION] == 100
    assert state.state == CoverState.OPEN

    # Position update to closed
    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.DEVICE_STATE_CHANGED.value,
                device_url=SHUTTER.device_url,
                device_states=[
                    {
                        "name": OverkizState.CORE_CLOSURE.value,
                        "type": 1,
                        "value": 100,
                    },
                    {
                        "name": OverkizState.CORE_TARGET_CLOSURE.value,
                        "type": 1,
                        "value": 100,
                    },
                    {
                        "name": OverkizState.CORE_MOVING.value,
                        "type": 6,
                        "value": False,
                    },
                    {
                        "name": OverkizState.CORE_OPEN_CLOSED.value,
                        "type": 3,
                        "value": OverkizCommandParam.CLOSED.value,
                    },
                ],
            )
        ],
    )

    state = hass.states.get(SHUTTER.entity_id)
    assert state.attributes[ATTR_CURRENT_POSITION] == 0
    assert state.state == CoverState.CLOSED

    # Execution tracking: state stays OPENING until execution completes
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: SHUTTER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(SHUTTER.entity_id).state == CoverState.OPENING

    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.DEVICE_STATE_CHANGED.value,
                device_url=SHUTTER.device_url,
                device_states=[
                    {
                        "name": OverkizState.CORE_CLOSURE.value,
                        "type": 1,
                        "value": 0,
                    },
                    {
                        "name": OverkizState.CORE_TARGET_CLOSURE.value,
                        "type": 1,
                        "value": 0,
                    },
                    {
                        "name": OverkizState.CORE_MOVING.value,
                        "type": 6,
                        "value": False,
                    },
                    {
                        "name": OverkizState.CORE_OPEN_CLOSED.value,
                        "type": 3,
                        "value": OverkizCommandParam.OPEN.value,
                    },
                ],
            )
        ],
    )
    assert hass.states.get(SHUTTER.entity_id).state == CoverState.OPENING

    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.EXECUTION_STATE_CHANGED.value,
                device_url=SHUTTER.device_url,
                exec_id="exec-1",
                new_state=ExecutionState.COMPLETED.value,
            )
        ],
    )
    assert hass.states.get(SHUTTER.entity_id).state == CoverState.OPEN

    # Unavailability propagates to entity state
    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.DEVICE_UNAVAILABLE.value, device_url=SHUTTER.device_url
            )
        ],
    )
    assert hass.states.get(SHUTTER.entity_id).state == STATE_UNAVAILABLE