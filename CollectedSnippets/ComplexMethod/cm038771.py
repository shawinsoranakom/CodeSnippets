async def async_request_openai_audio(
    request_func_input: RequestFuncInput,
    session: aiohttp.ClientSession,
    pbar: tqdm | None = None,
) -> RequestFuncOutput:
    # Lazy import without PlaceholderModule to avoid vllm dep.
    import soundfile

    api_url = request_func_input.api_url
    _validate_api_url(api_url, "OpenAI Audio API", {"transcriptions", "translations"})

    content = [{"type": "text", "text": request_func_input.prompt}]
    payload = {
        "model": request_func_input.model_name
        if request_func_input.model_name
        else request_func_input.model,
        "max_completion_tokens": request_func_input.output_len,
        "stream": True,
        "language": "en",
        # Flattened due to multipart/form-data
        "stream_include_usage": True,
        "stream_continuous_usage_stats": True,
    }
    _update_payload_common(payload, request_func_input)

    headers = _get_headers()
    _update_headers_common(headers, request_func_input)

    # Send audio file
    def to_bytes(y, sr):
        buffer = io.BytesIO()
        soundfile.write(buffer, y, sr, format="WAV")
        buffer.seek(0)
        return buffer

    mm_audio = request_func_input.multi_modal_content
    if not isinstance(mm_audio, dict) or "audio" not in mm_audio:
        raise TypeError("multi_modal_content must be a dict containing 'audio'")
    with to_bytes(*mm_audio["audio"]) as f:
        form = aiohttp.FormData()
        form.add_field("file", f, content_type="audio/wav")
        for key, value in payload.items():
            form.add_field(key, str(value))

        output = RequestFuncOutput()
        output.prompt_len = request_func_input.prompt_len
        output.input_audio_duration = soundfile.info(f).duration
        f.seek(0)

        generated_text = ""
        ttft = 0.0
        st = time.perf_counter()
        output.start_time = st
        most_recent_timestamp = st
        try:
            async with session.post(
                url=api_url, data=form, headers=headers
            ) as response:
                if response.status == 200:
                    handler = StreamedResponseHandler()

                    async for chunk_bytes in response.content.iter_any():
                        chunk_bytes = chunk_bytes.strip()
                        if not chunk_bytes:
                            continue

                        messages = handler.add_chunk(chunk_bytes)
                        for message in messages:
                            if type(message) is bytes:
                                message = message.decode("utf-8")
                            chunk = message.removeprefix("data: ")
                            if chunk != "[DONE]":
                                timestamp = time.perf_counter()
                                data = json.loads(chunk)

                                if choices := data.get("choices"):
                                    content = choices[0]["delta"].get("content")
                                    # First token
                                    if ttft == 0.0:
                                        ttft = timestamp - st
                                        output.ttft = ttft

                                    # Decoding phase
                                    else:
                                        output.itl.append(
                                            timestamp - most_recent_timestamp
                                        )

                                    generated_text += content or ""
                                elif usage := data.get("usage"):
                                    output.output_tokens = usage.get(
                                        "completion_tokens"
                                    )

                                most_recent_timestamp = timestamp

                    output.generated_text = generated_text
                    output.success = True
                    output.latency = most_recent_timestamp - st
                else:
                    output.error = response.reason or ""
                    output.success = False
        except Exception:
            output.success = False
            exc_info = sys.exc_info()
            output.error = "".join(traceback.format_exception(*exc_info))

    if pbar:
        pbar.update(1)
    return output