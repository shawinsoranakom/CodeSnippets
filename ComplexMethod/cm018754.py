async def test_switches_implementation(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_flexit_bacnet: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that the switch can be turned on and off."""

    await setup_with_selected_platforms(hass, mock_config_entry, [Platform.SWITCH])
    assert hass.states.get(ENTITY_ID) == snapshot(name=f"{ENTITY_ID}-state")

    # Set to off
    mock_flexit_bacnet.electric_heater = False

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mocked_method = mock_flexit_bacnet.disable_electric_heater
    assert len(mocked_method.mock_calls) == 1
    assert hass.states.get(ENTITY_ID).state == STATE_OFF

    # Set to on
    mock_flexit_bacnet.electric_heater = True

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mocked_method = mock_flexit_bacnet.enable_electric_heater
    assert len(mocked_method.mock_calls) == 1
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    # Error recovery, when turning off
    mock_flexit_bacnet.disable_electric_heater.side_effect = DecodingError

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: ENTITY_ID},
            blocking=True,
        )

    mocked_method = mock_flexit_bacnet.disable_electric_heater
    assert len(mocked_method.mock_calls) == 2

    mock_flexit_bacnet.disable_electric_heater.side_effect = None
    mock_flexit_bacnet.electric_heater = False

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    assert hass.states.get(ENTITY_ID).state == STATE_OFF

    # Error recovery, when turning on
    mock_flexit_bacnet.enable_electric_heater.side_effect = DecodingError

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_ID},
            blocking=True,
        )

    mocked_method = mock_flexit_bacnet.enable_electric_heater
    assert len(mocked_method.mock_calls) == 2

    mock_flexit_bacnet.enable_electric_heater.side_effect = None
    mock_flexit_bacnet.electric_heater = True

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    assert hass.states.get(ENTITY_ID).state == STATE_ON