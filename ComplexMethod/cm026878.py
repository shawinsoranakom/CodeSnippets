async def websocket_run(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a pipeline."""
    pipeline_id = msg.get("pipeline")
    try:
        pipeline = async_get_pipeline(hass, pipeline_id=pipeline_id)
    except PipelineNotFound:
        connection.send_error(
            msg["id"],
            "pipeline-not-found",
            f"Pipeline not found: id={pipeline_id}",
        )
        return

    timeout = msg.get("timeout", DEFAULT_PIPELINE_TIMEOUT)
    start_stage = PipelineStage(msg["start_stage"])
    end_stage = PipelineStage(msg["end_stage"])
    handler_id: int | None = None
    unregister_handler: Callable[[], None] | None = None
    wake_word_settings: WakeWordSettings | None = None
    audio_settings: AudioSettings | None = None

    # Arguments to PipelineInput
    input_args: dict[str, Any] = {
        "device_id": msg.get("device_id"),
    }

    if start_stage in (PipelineStage.WAKE_WORD, PipelineStage.STT):
        # Audio pipeline that will receive audio as binary websocket messages
        msg_input = msg["input"]
        audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
        incoming_sample_rate = msg_input["sample_rate"]
        wake_word_phrase: str | None = None

        if start_stage == PipelineStage.WAKE_WORD:
            wake_word_settings = WakeWordSettings(
                timeout=msg["input"].get("timeout", DEFAULT_WAKE_WORD_TIMEOUT),
                audio_seconds_to_buffer=msg_input.get("audio_seconds_to_buffer", 0),
            )
        elif start_stage == PipelineStage.STT:
            wake_word_phrase = msg["input"].get("wake_word_phrase")

        async def stt_stream() -> AsyncGenerator[bytes]:
            state = None

            # Yield until we receive an empty chunk
            while chunk := await audio_queue.get():
                if incoming_sample_rate != SAMPLE_RATE:
                    chunk, state = audioop.ratecv(
                        chunk,
                        SAMPLE_WIDTH,
                        SAMPLE_CHANNELS,
                        incoming_sample_rate,
                        SAMPLE_RATE,
                        state,
                    )
                yield chunk

        def handle_binary(
            _hass: HomeAssistant,
            _connection: websocket_api.ActiveConnection,
            data: bytes,
        ) -> None:
            # Forward to STT audio stream
            audio_queue.put_nowait(data)

        handler_id, unregister_handler = connection.async_register_binary_handler(
            handle_binary
        )

        # Audio input must be raw PCM at 16Khz with 16-bit mono samples
        input_args["stt_metadata"] = stt.SpeechMetadata(
            language=pipeline.stt_language or pipeline.language,
            format=stt.AudioFormats.WAV,
            codec=stt.AudioCodecs.PCM,
            bit_rate=stt.AudioBitRates.BITRATE_16,
            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
            channel=stt.AudioChannels.CHANNEL_MONO,
        )
        input_args["stt_stream"] = stt_stream()
        input_args["wake_word_phrase"] = wake_word_phrase

        # Audio settings
        audio_settings = AudioSettings(
            noise_suppression_level=msg_input.get("noise_suppression_level", 0),
            auto_gain_dbfs=msg_input.get("auto_gain_dbfs", 0),
            volume_multiplier=msg_input.get("volume_multiplier", 1.0),
            is_vad_enabled=not msg_input.get("no_vad", False),
        )
    elif start_stage == PipelineStage.INTENT:
        # Input to conversation agent
        input_args["intent_input"] = msg["input"]["text"]
    elif start_stage == PipelineStage.TTS:
        # Input to text-to-speech system
        input_args["tts_input"] = msg["input"]["text"]

    input_args["run"] = PipelineRun(
        hass,
        context=connection.context(msg),
        pipeline=pipeline,
        start_stage=start_stage,
        end_stage=end_stage,
        event_callback=lambda event: connection.send_event(msg["id"], event),
        runner_data={
            "stt_binary_handler_id": handler_id,
            "timeout": timeout,
        },
        wake_word_settings=wake_word_settings,
        audio_settings=audio_settings or AudioSettings(),
    )

    with chat_session.async_get_chat_session(
        hass, msg.get("conversation_id")
    ) as session:
        input_args["session"] = session
        pipeline_input = PipelineInput(**input_args)

        try:
            await pipeline_input.validate()
        except PipelineError as error:
            # Report more specific error when possible
            connection.send_error(msg["id"], error.code, error.message)
            return

        # Confirm subscription
        connection.send_result(msg["id"])

        run_task = hass.async_create_task(pipeline_input.execute())

        # Cancel pipeline if user unsubscribes
        connection.subscriptions[msg["id"]] = run_task.cancel

        try:
            # Task contains a timeout
            async with asyncio.timeout(timeout):
                await run_task
        except TimeoutError:
            pipeline_input.run.process_event(
                PipelineEvent(
                    PipelineEventType.ERROR,
                    {"code": "timeout", "message": "Timeout running pipeline"},
                )
            )
        finally:
            if unregister_handler is not None:
                # Unregister binary handler
                unregister_handler()