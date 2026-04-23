async def test_cover_tilt_services(
    hass: HomeAssistant,
    setup_overkiz_integration: SetupOverkizIntegration,
    mock_client: MockOverkizClient,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test tilt services for a pergola from a full user setup."""
    await setup_overkiz_integration(fixture=PERGOLA.fixture)

    state = hass.states.get(PERGOLA.entity_id)
    assert state
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.attributes["supported_features"] == (
        CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.STOP_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    mock_client.execute_command.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: PERGOLA.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(PERGOLA.entity_id).state == CoverState.OPENING
    assert_command_call(
        mock_client,
        device_url=PERGOLA.device_url,
        command_name="openSlats",
    )

    await async_deliver_events(
        hass,
        freezer,
        mock_client,
        [
            build_event(
                EventName.EXECUTION_STATE_CHANGED.value,
                device_url=PERGOLA.device_url,
                exec_id="exec-1",
                new_state=ExecutionState.COMPLETED.value,
            )
        ],
    )
    assert hass.states.get(PERGOLA.entity_id).state == CoverState.CLOSED

    mock_client.execute_command.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: PERGOLA.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(PERGOLA.entity_id).state == CoverState.CLOSING
    assert_command_call(
        mock_client,
        device_url=PERGOLA.device_url,
        command_name="closeSlats",
    )

    mock_client.execute_command.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: PERGOLA.entity_id},
        blocking=True,
    )
    assert_command_call(
        mock_client,
        device_url=PERGOLA.device_url,
        command_name="stop",
    )

    mock_client.execute_command.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: PERGOLA.entity_id, ATTR_TILT_POSITION: 40},
        blocking=True,
    )
    assert_command_call(
        mock_client,
        device_url=PERGOLA.device_url,
        command_name="setOrientation",
        parameters=[60],
    )