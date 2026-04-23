async def test_fans(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    aioclient_mock: AiohttpClientMocker,
    config_entry_factory: ConfigEntryFactoryType,
    mock_put_request: Callable[[str, str], AiohttpClientMocker],
    light_ws_data: WebsocketDataType,
) -> None:
    """Test that all supported fan entities are created."""
    with patch("homeassistant.components.deconz.PLATFORMS", [Platform.FAN]):
        config_entry = await config_entry_factory()

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)

    # Test states

    for speed, percent in (1, 25), (2, 50), (3, 75), (4, 100):
        await light_ws_data({"state": {"speed": speed}})
        assert hass.states.get("fan.ceiling_fan").state == STATE_ON
        assert hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == percent

    await light_ws_data({"state": {"speed": 0}})
    assert hass.states.get("fan.ceiling_fan").state == STATE_OFF
    assert hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE] == 0

    # Test service calls

    aioclient_mock = mock_put_request("/lights/0/state")

    # Service turn on fan using saved default_on_speed

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"speed": 4}

    # Service turn off fan

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"speed": 0}

    # Service turn on fan to 20%

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"speed": 1}

    # Service set fan percentage

    for percent, speed in (20, 1), (40, 2), (60, 3), (80, 4), (0, 0):
        aioclient_mock.mock_calls.clear()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: percent},
            blocking=True,
        )
        assert aioclient_mock.mock_calls[0][2] == {"speed": speed}

    # Events with an unsupported speed does not get converted

    await light_ws_data({"state": {"speed": 5}})
    assert hass.states.get("fan.ceiling_fan").state == STATE_ON
    assert not hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE]