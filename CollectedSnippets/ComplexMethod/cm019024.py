async def test_migrating_pipelines(
    hass: HomeAssistant,
    cloud: MagicMock,
    hass_client: ClientSessionGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test migrating pipelines when cloud stt entity is added."""
    entity_id = "stt.home_assistant_cloud"
    cloud.voice.process_stt = AsyncMock(
        return_value=STTResponse(True, "Turn the Kitchen Lights on")
    )
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": "assist_pipeline.pipelines",
        "data": deepcopy(PIPELINE_DATA),
    }

    assert await async_setup_component(hass, "assist_pipeline", {})
    assert await async_setup_component(hass, DOMAIN, {"cloud": {}})
    await hass.async_block_till_done()

    await cloud.login("test-user", "test-pass")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN

    # The stt/tts engines should have been updated to the new cloud engine ids.
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["stt_engine"] == entity_id
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["tts_engine"]
        == "tts.home_assistant_cloud"
    )

    # The other items should stay the same.
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["conversation_engine"]
        == "conversation_engine_1"
    )
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["conversation_language"]
        == "language_1"
    )
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["id"]
        == "01GX8ZWBAQYWNB1XV3EXEZ75DY"
    )
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["language"] == "language_1"
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["name"] == "Home Assistant Cloud"
    )
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["stt_language"] == "language_1"
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["tts_language"] == "language_1"
    assert (
        hass_storage[STORAGE_KEY]["data"]["items"][0]["tts_voice"]
        == "Arnold Schwarzenegger"
    )
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["wake_word_entity"] is None
    assert hass_storage[STORAGE_KEY]["data"]["items"][0]["wake_word_id"] is None
    assert hass_storage[STORAGE_KEY]["data"]["items"][1] == PIPELINE_DATA["items"][1]
    assert hass_storage[STORAGE_KEY]["data"]["items"][2] == PIPELINE_DATA["items"][2]