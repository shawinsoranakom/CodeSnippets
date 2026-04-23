async def test_wake_word_select(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test wake word select."""
    device_config = AssistSatelliteConfiguration(
        available_wake_words=[
            AssistSatelliteWakeWord("okay_nabu", "Okay Nabu", ["en"]),
            AssistSatelliteWakeWord("hey_jarvis", "Hey Jarvis", ["en"]),
            AssistSatelliteWakeWord("hey_mycroft", "Hey Mycroft", ["en"]),
        ],
        active_wake_words=["hey_jarvis"],
        max_active_wake_words=2,
    )
    mock_client.get_voice_assistant_configuration.return_value = device_config

    # Wrap mock so we can tell when it's done
    configuration_set = asyncio.Event()

    async def wrapper(*args, **kwargs):
        # Update device config because entity will request it after update
        device_config.active_wake_words = kwargs["active_wake_words"]
        configuration_set.set()

    mock_client.set_voice_assistant_configuration = AsyncMock(side_effect=wrapper)

    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        device_info={
            "voice_assistant_feature_flags": VoiceAssistantFeature.VOICE_ASSISTANT
            | VoiceAssistantFeature.ANNOUNCE
        },
    )
    await hass.async_block_till_done()

    satellite = get_satellite_entity(hass, mock_device.device_info.mac_address)
    assert satellite is not None
    assert satellite.async_get_configuration().active_wake_words == ["hey_jarvis"]

    # First wake word should be selected by default
    state = hass.states.get("select.test_wake_word")
    assert state is not None
    assert state.state == "Hey Jarvis"

    # Changing the select should set the active wake word
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word", "option": "Okay Nabu"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("select.test_wake_word")
    assert state is not None
    assert state.state == "Okay Nabu"

    # Wait for device config to be updated
    async with asyncio.timeout(1):
        await configuration_set.wait()

    # Satellite config should have been updated
    assert satellite.async_get_configuration().active_wake_words == ["okay_nabu"]

    # No secondary wake word should be selected by default
    state = hass.states.get("select.test_wake_word_2")
    assert state is not None
    assert state.state == NO_WAKE_WORD

    # Changing the secondary select should add an active wake word
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word_2", "option": "Hey Jarvis"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("select.test_wake_word_2")
    assert state is not None
    assert state.state == "Hey Jarvis"

    # Wait for device config to be updated
    async with asyncio.timeout(1):
        await configuration_set.wait()

    # Satellite config should have been updated
    assert set(satellite.async_get_configuration().active_wake_words) == {
        "okay_nabu",
        "hey_jarvis",
    }

    # Remove the secondary wake word
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word_2", "option": NO_WAKE_WORD},
        blocking=True,
    )
    await hass.async_block_till_done()

    async with asyncio.timeout(1):
        await configuration_set.wait()

    # Only primary wake word remains
    assert satellite.async_get_configuration().active_wake_words == ["okay_nabu"]

    # Remove the primary wake word
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word", "option": NO_WAKE_WORD},
        blocking=True,
    )
    await hass.async_block_till_done()

    async with asyncio.timeout(1):
        await configuration_set.wait()

    # No active wake word remain
    assert not satellite.async_get_configuration().active_wake_words