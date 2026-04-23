async def test_get_pipeline(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, init_components
) -> None:
    """Test we can get a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "conversation_engine": "conversation.home_assistant",
        "conversation_language": "en",
        "id": ANY,
        "language": "en",
        "name": "Home Assistant",
        "stt_engine": "stt.mock_stt",
        "stt_language": "en-US",
        "tts_engine": "tts.test",
        "tts_language": "en_US",
        "tts_voice": None,
        "wake_word_entity": None,
        "wake_word_id": None,
        "prefer_local_intents": False,
    }

    # Get conversation agent as pipeline
    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": "conversation.home_assistant",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "conversation_engine": "conversation.home_assistant",
        "conversation_language": "en",
        "id": ANY,
        "language": "en",
        "name": "Home Assistant",
        # It found these defaults
        "stt_engine": "stt.mock_stt",
        "stt_language": "en-US",
        "tts_engine": "tts.test",
        "tts_language": "en_US",
        "tts_voice": None,
        "wake_word_entity": None,
        "wake_word_id": None,
        "prefer_local_intents": False,
    }

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": "no_such_pipeline",
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
            "prefer_local_intents": False,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    pipeline_id = msg["result"]["id"]
    assert len(pipeline_store.data) == 2

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/get",
            "pipeline_id": pipeline_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "conversation_engine": "test_conversation_engine",
        "conversation_language": "test_language",
        "id": pipeline_id,
        "language": "test_language",
        "name": "test_name",
        "stt_engine": "test_stt_engine",
        "stt_language": "test_language",
        "tts_engine": "test_tts_engine",
        "tts_language": "test_language",
        "tts_voice": "Arnold Schwarzenegger",
        "wake_word_entity": "wakeword_entity_1",
        "wake_word_id": "wakeword_id_1",
        "prefer_local_intents": False,
    }