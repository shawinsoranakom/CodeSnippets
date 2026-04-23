async def test_stream_tts_with_request_ids(
    setup: AsyncMock,
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    capture_stream_calls,
    stream_sentence_helpers,
    model_id: str,
    message: list[list[str]],
    chunks: list[bytes],
    request_ids: list[str],
) -> None:
    """Test streaming TTS with request-id stitching."""
    calls, set_next_return, patch_stream = capture_stream_calls

    # Access the TTS entity as in your existing tests; adjust if you use a fixture instead
    tts_entity = hass.data[tts.DOMAIN].get_entity("tts.elevenlabs_text_to_speech")
    patch_stream(tts_entity)

    # Use a queue to control when each part is yielded
    queue = asyncio.Queue()
    prev_request_ids: deque[str] = deque(maxlen=3)  # keep last 3 request IDs
    sentence_iter = iter(zip(message, chunks, request_ids, strict=False))
    get_next_part, message_gen = stream_sentence_helpers(sentence_iter, queue)
    options = {tts.ATTR_VOICE: "voice1", "model": model_id}
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
        assert "previous_text" not in calls[-1]  # no previous_text for first sentence
        assert "next_text" not in calls[-1]  # no next_text for first
        assert calls[-1].get("previous_request_ids", []) == (
            [] if len(calls) == 1 else list(prev_request_ids)
        )
        if request_id:
            prev_request_ids.append(request_id or "")
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