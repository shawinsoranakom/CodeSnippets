async def test_secondary_pipeline(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that the secondary pipeline is used when the secondary wake word is given."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    pipeline_data = hass.data[KEY_ASSIST_PIPELINE]
    pipeline_id_to_name: dict[str, str] = {}
    for pipeline_name in ("Primary Pipeline", "Secondary Pipeline"):
        pipeline = await pipeline_data.pipeline_store.async_create_item(
            {
                "name": pipeline_name,
                "language": "en-US",
                "conversation_engine": None,
                "conversation_language": "en-US",
                "tts_engine": None,
                "tts_language": None,
                "tts_voice": None,
                "stt_engine": None,
                "stt_language": None,
                "wake_word_entity": None,
                "wake_word_id": None,
            }
        )
        pipeline_id_to_name[pipeline.id] = pipeline_name

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

    # Set primary/secondary wake words and assistants
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word", "option": "Okay Nabu"},
        blocking=True,
    )
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_assistant", "option": "Primary Pipeline"},
        blocking=True,
    )
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_wake_word_2", "option": "Hey Jarvis"},
        blocking=True,
    )
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.test_assistant_2",
            "option": "Secondary Pipeline",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    async def get_pipeline(wake_word_phrase):
        with patch(
            "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream",
        ) as mock_pipeline_from_audio_stream:
            await satellite.handle_pipeline_start(
                conversation_id="",
                flags=0,
                audio_settings=VoiceAssistantAudioSettings(),
                wake_word_phrase=wake_word_phrase,
            )

            mock_pipeline_from_audio_stream.assert_called_once()
            kwargs = mock_pipeline_from_audio_stream.call_args_list[0].kwargs
            return pipeline_id_to_name[kwargs["pipeline_id"]]

    # Primary pipeline is the default
    for wake_word_phrase in (None, "Okay Nabu"):
        assert (await get_pipeline(wake_word_phrase)) == "Primary Pipeline"

    # Secondary pipeline requires secondary wake word
    assert (await get_pipeline("Hey Jarvis")) == "Secondary Pipeline"

    # Primary pipeline should be restored after
    assert (await get_pipeline(None)) == "Primary Pipeline"