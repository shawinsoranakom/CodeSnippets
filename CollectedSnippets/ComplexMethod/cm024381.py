async def test_cached_supported_features(hass: HomeAssistant, client) -> None:
    """Test test supported features."""
    client.tv_state.is_on = False
    client.tv_state.sound_output = None
    supported = (
        SUPPORT_WEBOSTV | SUPPORT_WEBOSTV_VOLUME | MediaPlayerEntityFeature.TURN_ON
    )
    mock_restore_cache(
        hass,
        [
            State(
                ENTITY_ID,
                STATE_OFF,
                attributes={
                    ATTR_SUPPORTED_FEATURES: supported,
                },
            )
        ],
    )
    await setup_webostv(hass)
    await client.mock_state_update()

    # TV off, restored state supports mute, step
    # validate MediaPlayerEntityFeature.TURN_ON is not cached
    attrs = hass.states.get(ENTITY_ID).attributes

    assert (
        attrs[ATTR_SUPPORTED_FEATURES] == supported & ~MediaPlayerEntityFeature.TURN_ON
    )

    # TV on, support volume mute, step
    client.tv_state.is_on = True
    client.tv_state.sound_output = "external_speaker"
    await client.mock_state_update()

    supported = SUPPORT_WEBOSTV | SUPPORT_WEBOSTV_VOLUME
    attrs = hass.states.get(ENTITY_ID).attributes

    assert attrs[ATTR_SUPPORTED_FEATURES] == supported

    # TV off, support volume mute, step
    client.tv_state.is_on = False
    client.tv_state.sound_output = None
    await client.mock_state_update()

    supported = SUPPORT_WEBOSTV | SUPPORT_WEBOSTV_VOLUME
    attrs = hass.states.get(ENTITY_ID).attributes

    assert attrs[ATTR_SUPPORTED_FEATURES] == supported

    # TV on, support volume mute, step, set
    client.tv_state.is_on = True
    client.tv_state.sound_output = "speaker"
    await client.mock_state_update()

    supported = (
        SUPPORT_WEBOSTV | SUPPORT_WEBOSTV_VOLUME | MediaPlayerEntityFeature.VOLUME_SET
    )
    attrs = hass.states.get(ENTITY_ID).attributes

    assert attrs[ATTR_SUPPORTED_FEATURES] == supported

    # TV off, support volume mute, step, set
    client.tv_state.is_on = False
    client.tv_state.sound_output = None
    await client.mock_state_update()

    supported = (
        SUPPORT_WEBOSTV | SUPPORT_WEBOSTV_VOLUME | MediaPlayerEntityFeature.VOLUME_SET
    )
    attrs = hass.states.get(ENTITY_ID).attributes

    assert attrs[ATTR_SUPPORTED_FEATURES] == supported

    # Test support turn on is updated on cached state
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "webostv.turn_on",
                        "entity_id": ENTITY_ID,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": ENTITY_ID,
                            "id": "{{ trigger.id }}",
                        },
                    },
                },
            ],
        },
    )
    await client.mock_state_update()

    attrs = hass.states.get(ENTITY_ID).attributes

    assert (
        attrs[ATTR_SUPPORTED_FEATURES] == supported | MediaPlayerEntityFeature.TURN_ON
    )