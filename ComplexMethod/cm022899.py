async def test_delete_pipeline(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, init_components
) -> None:
    """Test we can delete a pipeline."""
    client = await hass_ws_client(hass)
    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_store = pipeline_data.pipeline_store

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
    pipeline_id_1 = msg["result"]["id"]

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
            "wake_word_entity": "wakeword_entity_2",
            "wake_word_id": "wakeword_id_2",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    pipeline_id_2 = msg["result"]["id"]

    assert len(pipeline_store.data) == 3

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/set_preferred",
            "pipeline_id": pipeline_id_1,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_1,
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_allowed",
        "message": f"Item {pipeline_id_1} preferred.",
    }

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_2,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert len(pipeline_store.data) == 2

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/delete",
            "pipeline_id": pipeline_id_2,
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_found",
        "message": f"Unable to find pipeline_id {pipeline_id_2}",
    }