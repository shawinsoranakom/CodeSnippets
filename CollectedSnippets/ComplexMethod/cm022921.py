async def test_load_pipelines(hass: HomeAssistant) -> None:
    """Make sure that we can load/save data correctly."""

    pipelines = [
        {
            "conversation_engine": "conversation_engine_1",
            "conversation_language": "language_1",
            "language": "language_1",
            "name": "name_1",
            "stt_engine": "stt_engine_1",
            "stt_language": "language_1",
            "tts_engine": "tts_engine_1",
            "tts_language": "language_1",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        },
        {
            "conversation_engine": "conversation_engine_2",
            "conversation_language": "language_2",
            "language": "language_2",
            "name": "name_2",
            "stt_engine": "stt_engine_2",
            "stt_language": "language_1",
            "tts_engine": "tts_engine_2",
            "tts_language": "language_2",
            "tts_voice": "The Voice",
            "wake_word_entity": "wakeword_entity_2",
            "wake_word_id": "wakeword_id_2",
        },
        {
            "conversation_engine": "conversation_engine_3",
            "conversation_language": "language_3",
            "language": "language_3",
            "name": "name_3",
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": "wakeword_entity_3",
            "wake_word_id": "wakeword_id_3",
        },
    ]

    pipeline_data: PipelineData = hass.data[DOMAIN]
    store1 = pipeline_data.pipeline_store
    pipeline_ids = [
        (await store1.async_create_item(pipeline)).id for pipeline in pipelines
    ]
    assert len(store1.data) == 4  # 3 manually created plus a default pipeline
    assert store1.async_get_preferred_item() == list(store1.data)[0]

    await store1.async_delete_item(pipeline_ids[1])
    assert len(store1.data) == 3

    store2 = PipelineStorageCollection(
        PipelineStore(
            hass, STORAGE_VERSION, STORAGE_KEY, minor_version=STORAGE_VERSION_MINOR
        )
    )
    await flush_store(store1.store)
    await store2.async_load()

    assert len(store2.data) == 3

    assert store1.data is not store2.data
    assert store1.data == store2.data
    assert store1.async_get_preferred_item() == store2.async_get_preferred_item()