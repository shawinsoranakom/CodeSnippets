async def _process_tts_stream(
        self, request: TTSAudioRequest
    ) -> AsyncGenerator[bytes]:
        """Generate speech from an incoming message."""
        text_stream = request.message_gen
        boundary_detector = SentenceBoundaryDetector()
        sentences: list[str] = []
        sentences_ready = asyncio.Event()
        sentences_complete = False

        language_code: str | None = request.language
        voice_id = request.options.get(ATTR_VOICE, self._default_voice_id)
        model = request.options.get(ATTR_MODEL, self._model.model_id)

        use_request_ids = model not in MODELS_PREVIOUS_INFO_NOT_SUPPORTED
        previous_request_ids: deque[str] = deque(maxlen=MAX_REQUEST_IDS)

        base_stream_params = {
            "voice_id": voice_id,
            "model_id": model,
            "output_format": "mp3_44100_128",
            "voice_settings": self._voice_settings,
        }
        if language_code:
            base_stream_params["language_code"] = language_code

        _LOGGER.debug("Starting TTS Stream with options: %s", base_stream_params)

        async def _add_sentences() -> None:
            nonlocal sentences_complete

            try:
                # Text chunks may not be on word or sentence boundaries
                async for text_chunk in text_stream:
                    for sentence in boundary_detector.add_chunk(text_chunk):
                        if not sentence.strip():
                            continue

                        sentences.append(sentence)

                    if not sentences:
                        continue

                    sentences_ready.set()

                # Final sentence
                if text := boundary_detector.finish():
                    sentences.append(text)
            finally:
                sentences_complete = True
                sentences_ready.set()

        _add_sentences_task = self.hass.async_create_background_task(
            _add_sentences(), name="elevenlabs_tts_add_sentences"
        )

        # Process new sentences as they're available, but synthesize the first
        # one immediately. While that's playing, synthesize (up to) the next 3
        # sentences. After that, synthesize all completed sentences as they're
        # available.
        sentence_schedule = [1, 3]
        while True:
            await sentences_ready.wait()

            # Don't wait again if no more sentences are coming
            if not sentences_complete:
                sentences_ready.clear()

            if not sentences:
                if sentences_complete:
                    # Exit TTS loop
                    _LOGGER.debug("No more sentences to process")
                    break

                # More sentences may be coming
                continue

            new_sentences = sentences[:]
            sentences.clear()

            while new_sentences:
                if sentence_schedule:
                    max_sentences = sentence_schedule.pop(0)
                    sentences_to_process = new_sentences[:max_sentences]
                    new_sentences = new_sentences[len(sentences_to_process) :]
                else:
                    # Process all available sentences together
                    sentences_to_process = new_sentences[:]
                    new_sentences.clear()

                # Combine all new sentences completed to this point
                text = " ".join(sentences_to_process).strip()

                if not text:
                    continue

                # Build kwargs common to both modes
                kwargs: dict[str, Any] = base_stream_params | {
                    "text": text,
                }

                # Provide previous_request_ids if supported.
                if previous_request_ids:
                    # Send previous request ids.
                    kwargs["previous_request_ids"] = list(previous_request_ids)

                # Synthesize audio while text chunks are still being accumulated
                _LOGGER.debug("Synthesizing TTS for text: %s", text)
                try:
                    async with self._client.text_to_speech.with_raw_response.stream(
                        **kwargs
                    ) as stream:
                        async for chunk_bytes in stream.data:
                            yield chunk_bytes

                        if use_request_ids:
                            if (rid := stream.headers.get("request-id")) is not None:
                                previous_request_ids.append(rid)
                            else:
                                _LOGGER.debug(
                                    "No request-id returned from server; clearing previous requests"
                                )
                                previous_request_ids.clear()
                except ApiError as exc:
                    _LOGGER.warning(
                        "Error during processing of TTS request %s", exc, exc_info=True
                    )
                    _add_sentences_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await _add_sentences_task
                    raise HomeAssistantError(exc) from exc

                # Capture and store server request-id for next calls (only when supported)
                _LOGGER.debug("Completed TTS stream for text: %s", text)

        _LOGGER.debug("Completed TTS stream")