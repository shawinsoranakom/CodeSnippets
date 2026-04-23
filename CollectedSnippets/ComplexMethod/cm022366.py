async def test_stream_tts_without_previous_info(
    setup: AsyncMock,
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    capture_stream_calls,
    stream_sentence_helpers,
    monkeypatch: pytest.MonkeyPatch,
    message: list[list[str]],
    chunks: list[bytes],
    request_ids: list[str],
) -> None:
    """Test streaming TTS without request-id stitching (eleven_v3)."""
    calls, set_next_return, patch_stream = capture_stream_calls
    tts_entity = hass.data[tts.DOMAIN].get_entity("tts.elevenlabs_text_to_speech")
    patch_stream(tts_entity)
    monkeypatch.setattr(
        "homeassistant.components.elevenlabs.tts.MODELS_PREVIOUS_INFO_NOT_SUPPORTED",
        ("model1",),
        raising=False,
    )

    queue = asyncio.Queue()
    sentence_iter = iter(zip(message, chunks, request_ids, strict=False))
    get_next_part, message_gen = stream_sentence_helpers(sentence_iter, queue)
    options = {tts.ATTR_VOICE: "voice1", "model": "model1"}
    req = TTSAudioRequest(message_gen=message_gen(), language="en", options=options)

    resp = await tts_entity.async_stream_tts_audio(req)
    assert resp.extension == "mp3"

    item, chunk, request_id = await get_next_part()
    if item is not None:
        for part in item:
            await queue.put(part)
    else:
        await queue.put(None)

    set_next_return(chunks=[chunk], request_id=request_id)
    next_item, next_chunk, next_request_id = await get_next_part()
    # Consume bytes; after first chunk, switch next return to emulate second call
    async for b in resp.data_gen:
        assert b == chunk  # each sentence yields its first chunk immediately
        assert "previous_request_ids" not in calls[-1]  # no previous_request_ids

        item, chunk, request_id = next_item, next_chunk, next_request_id
        if item is not None:
            for part in item:
                await queue.put(part)
            set_next_return(chunks=[chunk], request_id=request_id)
            next_item, next_chunk, next_request_id = await get_next_part()
            if item is None:
                await queue.put(None)
        else:
            await queue.put(None)

    # We expect two stream() invocations (one per sentence batch)
    assert len(calls) == len(message)