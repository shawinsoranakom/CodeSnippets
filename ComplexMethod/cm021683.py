async def test_proactive_mode_filter_states(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test all the cases that filter states."""
    aioclient_mock.post(TEST_URL, text="", status=202)
    config = get_default_config(hass)
    await state_report.async_enable_proactive_mode(hass, config)

    # First state should report
    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )
    await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 1

    aioclient_mock.clear_requests()

    # Second one shouldn't
    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )
    assert len(aioclient_mock.mock_calls) == 0

    # hass not running should not report
    current_state = hass.state
    hass.set_state(core.CoreState.stopping)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    hass.set_state(current_state)
    assert len(aioclient_mock.mock_calls) == 0

    # unsupported entity should not report
    with patch.dict(
        "homeassistant.components.alexa.state_report.ENTITY_ADAPTERS", {}, clear=True
    ):
        hass.states.async_set(
            "binary_sensor.test_contact",
            "on",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 0

    # Not exposed by config should not report
    with patch.object(config, "should_expose", return_value=False):
        hass.states.async_set(
            "binary_sensor.test_contact",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 0

    # Removing an entity
    hass.states.async_remove("binary_sensor.test_contact")
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 0

    # If serializes to same properties, it should not report
    aioclient_mock.post(TEST_URL, text="", status=202)
    with patch(
        "homeassistant.components.alexa.entities.AlexaEntity.serialize_properties",
        return_value=[{"same": "info"}],
    ):
        hass.states.async_set(
            "binary_sensor.same_serialize",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        hass.states.async_set(
            "binary_sensor.same_serialize",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )

        await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 1