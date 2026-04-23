async def generate_audio(
    payload: ChatCompletionRequest,
    request: Request,
    current_subject: str = Depends(get_current_subject),
):
    """
    Generate audio (TTS) from the latest user message.
    Returns a JSON response with base64-encoded WAV audio.
    Works with both GGUF (llama-server) and Unsloth/transformers backends.
    """
    import base64

    # Extract text from the last user message
    _, chat_messages, _ = _extract_content_parts(payload.messages)
    if not chat_messages:
        raise HTTPException(status_code = 400, detail = "No messages provided.")
    last_user_msg = next(
        (m for m in reversed(chat_messages) if m["role"] == "user"), None
    )
    if not last_user_msg:
        raise HTTPException(status_code = 400, detail = "No user message found.")
    text = last_user_msg["content"]

    # Pick backend — both return (wav_bytes, sample_rate)
    llama_backend = get_llama_cpp_backend()
    if llama_backend.is_loaded and getattr(llama_backend, "_is_audio", False):
        model_name = llama_backend.model_identifier
        gen = lambda: llama_backend.generate_audio_response(
            text = text,
            audio_type = llama_backend._audio_type,
            temperature = payload.temperature,
            top_p = payload.top_p,
            top_k = payload.top_k,
            min_p = payload.min_p,
            max_new_tokens = payload.max_tokens or 2048,
            repetition_penalty = payload.repetition_penalty,
        )
    else:
        backend = get_inference_backend()
        if not backend.active_model_name:
            raise HTTPException(status_code = 400, detail = "No model loaded.")
        model_info = backend.models.get(backend.active_model_name, {})
        if not model_info.get("is_audio"):
            raise HTTPException(
                status_code = 400, detail = "Active model is not an audio model."
            )
        model_name = backend.active_model_name
        gen = lambda: backend.generate_audio_response(
            text = text,
            temperature = payload.temperature,
            top_p = payload.top_p,
            top_k = payload.top_k,
            min_p = payload.min_p,
            max_new_tokens = payload.max_tokens or 2048,
            repetition_penalty = payload.repetition_penalty,
            use_adapter = payload.use_adapter,
        )

    try:
        wav_bytes, sample_rate = await asyncio.get_event_loop().run_in_executor(
            None, gen
        )
    except Exception as e:
        logger.error(f"Audio generation error: {e}", exc_info = True)
        raise HTTPException(status_code = 500, detail = str(e))

    audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
    return JSONResponse(
        content = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion.audio",
            "model": model_name,
            "audio": {"data": audio_b64, "format": "wav", "sample_rate": sample_rate},
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f'[Generated audio from: "{text[:100]}"]',
                    },
                    "finish_reason": "stop",
                }
            ],
        }
    )