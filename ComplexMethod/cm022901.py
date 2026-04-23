async def test_update_pipeline(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, init_components
) -> None:
    """Test we can list pipelines."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": "no_such_pipeline",
            "stt_engine": "new_stt_engine",
            "stt_language": "new_stt_language",
            "tts_engine": "new_tts_engine",
            "tts_language": "new_tts_language",
            "tts_voice": "new_tts_voice",
            "wake_word_entity": "new_wakeword_entity",
            "wake_word_id": "new_wakeword_id",
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_found",
        "message": "Unable to find pipeline_id no_such_pipeline",
    }

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": "test_conversation_engine",
            "conversation_language": "test_language",
            "language": "test_language",
            "name": "test_name",
            "stt_engine": "test_stt_engine",
            "stt_language": "test_language",
            "tts_engine": "test_tts_engine",
            "tts_language": "test_language",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": "wakeword_entity_1",
            "wake_word_id": "wakeword_id_1",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    pipeline_id = msg["result"]["id"]
    assert len(pipeline_store.data) == 2

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": pipeline_id,
            "stt_engine": "new_stt_engine",
            "stt_language": "new_stt_language",
            "tts_engine": "new_tts_engine",
            "tts_language": "new_tts_language",
            "tts_voice": "new_tts_voice",
            "wake_word_entity": "new_wakeword_entity",
            "wake_word_id": "new_wakeword_id",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "conversation_engine": "new_conversation_engine",
        "conversation_language": "new_conversation_language",
        "id": pipeline_id,
        "language": "new_language",
        "name": "new_name",
        "stt_engine": "new_stt_engine",
        "stt_language": "new_stt_language",
        "tts_engine": "new_tts_engine",
        "tts_language": "new_tts_language",
        "tts_voice": "new_tts_voice",
        "wake_word_entity": "new_wakeword_entity",
        "wake_word_id": "new_wakeword_id",
        "prefer_local_intents": False,
    }

    assert len(pipeline_store.data) == 2
    pipeline = pipeline_store.data[pipeline_id]
    assert pipeline == Pipeline(
        conversation_engine="new_conversation_engine",
        conversation_language="new_conversation_language",
        id=pipeline_id,
        language="new_language",
        name="new_name",
        stt_engine="new_stt_engine",
        stt_language="new_stt_language",
        tts_engine="new_tts_engine",
        tts_language="new_tts_language",
        tts_voice="new_tts_voice",
        wake_word_entity="new_wakeword_entity",
        wake_word_id="new_wakeword_id",
    )

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/update",
            "conversation_engine": "new_conversation_engine",
            "conversation_language": "new_conversation_language",
            "language": "new_language",
            "name": "new_name",
            "pipeline_id": pipeline_id,
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "conversation_engine": "new_conversation_engine",
        "conversation_language": "new_conversation_language",
        "id": pipeline_id,
        "language": "new_language",
        "name": "new_name",
        "stt_engine": None,
        "stt_language": None,
        "tts_engine": None,
        "tts_language": None,
        "tts_voice": None,
        "wake_word_entity": None,
        "wake_word_id": None,
        "prefer_local_intents": False,
    }

    pipeline = pipeline_store.data[pipeline_id]
    assert pipeline == Pipeline(
        conversation_engine="new_conversation_engine",
        conversation_language="new_conversation_language",
        id=pipeline_id,
        language="new_language",
        name="new_name",
        stt_engine=None,
        stt_language=None,
        tts_engine=None,
        tts_language=None,
        tts_voice=None,
        wake_word_entity=None,
        wake_word_id=None,
    )