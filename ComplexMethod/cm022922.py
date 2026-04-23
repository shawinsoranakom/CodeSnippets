async def test_update_pipeline(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test async_update_pipeline."""
    assert await async_setup_component(hass, "assist_pipeline", {})

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    assert pipelines == [
        Pipeline(
            conversation_engine="conversation.home_assistant",
            conversation_language="en",
            id=ANY,
            language="en",
            name="Home Assistant",
            stt_engine=None,
            stt_language=None,
            tts_engine=None,
            tts_language=None,
            tts_voice=None,
            wake_word_entity=None,
            wake_word_id=None,
        )
    ]

    pipeline = pipelines[0]
    await async_update_pipeline(
        hass,
        pipeline,
        conversation_engine="homeassistant_1",
        conversation_language="de",
        language="de",
        name="Home Assistant 1",
        stt_engine="stt.test_1",
        stt_language="de",
        tts_engine="test_1",
        tts_language="de",
        tts_voice="test_voice",
        wake_word_entity="wake_work.test_1",
        wake_word_id="wake_word_id_1",
    )

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    pipeline = pipelines[0]
    assert pipelines == [
        Pipeline(
            conversation_engine="homeassistant_1",
            conversation_language="de",
            id=pipeline.id,
            language="de",
            name="Home Assistant 1",
            stt_engine="stt.test_1",
            stt_language="de",
            tts_engine="test_1",
            tts_language="de",
            tts_voice="test_voice",
            wake_word_entity="wake_work.test_1",
            wake_word_id="wake_word_id_1",
        )
    ]
    assert len(hass_storage[STORAGE_KEY]["data"]["items"]) == 1
    assert hass_storage[STORAGE_KEY]["data"]["items"][0] == {
        "conversation_engine": "homeassistant_1",
        "conversation_language": "de",
        "id": pipeline.id,
        "language": "de",
        "name": "Home Assistant 1",
        "stt_engine": "stt.test_1",
        "stt_language": "de",
        "tts_engine": "test_1",
        "tts_language": "de",
        "tts_voice": "test_voice",
        "wake_word_entity": "wake_work.test_1",
        "wake_word_id": "wake_word_id_1",
        "prefer_local_intents": False,
    }

    await async_update_pipeline(
        hass,
        pipeline,
        stt_engine="stt.test_2",
        stt_language="en",
        tts_engine="test_2",
        tts_language="en",
    )

    pipelines = async_get_pipelines(hass)
    pipelines = list(pipelines)
    assert pipelines == [
        Pipeline(
            conversation_engine="homeassistant_1",
            conversation_language="de",
            id=pipeline.id,
            language="de",
            name="Home Assistant 1",
            stt_engine="stt.test_2",
            stt_language="en",
            tts_engine="test_2",
            tts_language="en",
            tts_voice="test_voice",
            wake_word_entity="wake_work.test_1",
            wake_word_id="wake_word_id_1",
        )
    ]
    assert len(hass_storage[STORAGE_KEY]["data"]["items"]) == 1
    assert hass_storage[STORAGE_KEY]["data"]["items"][0] == {
        "conversation_engine": "homeassistant_1",
        "conversation_language": "de",
        "id": pipeline.id,
        "language": "de",
        "name": "Home Assistant 1",
        "stt_engine": "stt.test_2",
        "stt_language": "en",
        "tts_engine": "test_2",
        "tts_language": "en",
        "tts_voice": "test_voice",
        "wake_word_entity": "wake_work.test_1",
        "wake_word_id": "wake_word_id_1",
        "prefer_local_intents": False,
    }