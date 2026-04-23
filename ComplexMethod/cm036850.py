async def test_empty_commit_does_not_crash_engine(
    model_name, mary_had_lamb_audio_chunks, rocm_aiter_fa_attention
):
    """Test that committing without audio does not crash the engine.

    Regression test for https://github.com/vllm-project/vllm/issues/34532.
    An empty commit (no prior input_audio_buffer.append) used to trigger
    ``AssertionError: For realtime you must provide a multimodal_embedding
    at every step`` which killed the entire engine process, disconnecting
    every connected client.
    """
    server_args = ["--enforce-eager", "--max-model-len", "2048"]

    if model_name.startswith("mistralai"):
        server_args += MISTRAL_FORMAT_ARGS

    add_attention_backend(server_args, rocm_aiter_fa_attention)

    with RemoteOpenAIServer(
        model_name, server_args, env_dict=REALTIME_ENV_OVERRIDES
    ) as remote_server:
        ws_url = _get_websocket_url(remote_server)

        # --- First connection: empty commit (no audio appended) ----------
        async with websockets.connect(ws_url) as ws:
            event = await receive_event(ws, timeout=30.0)
            assert event["type"] == "session.created"

            await send_event(ws, {"type": "session.update", "model": model_name})

            try:
                while True:
                    event = await receive_event(ws, timeout=5.0)
                    if event["type"] == "session.updated":
                        break
            except TimeoutError:
                warnings.warn(
                    f"session.updated not received within {5.0}s after "
                    "session.update. The server may not implement this event.",
                    stacklevel=2,
                )

            # Start generation without sending any audio
            await send_event(ws, {"type": "input_audio_buffer.commit"})

            # Immediately signal end-of-audio
            await send_event(ws, {"type": "input_audio_buffer.commit", "final": True})

            # We should get *some* response (error or empty transcription),
            # but the engine must NOT crash.
            # (ROCm) Use generous timeout for first request (aiter JIT compilation)
            event = await receive_event(ws, timeout=360.0)
            assert event["type"] in (
                "error",
                "transcription.done",
                "transcription.delta",
            )

        # --- Second connection: normal transcription ---------------------
        # Verifies the engine is still alive after the empty commit above.
        async with websockets.connect(ws_url) as ws:
            event = await receive_event(ws, timeout=30.0)
            assert event["type"] == "session.created"

            await send_event(ws, {"type": "session.update", "model": model_name})

            try:
                while True:
                    event = await receive_event(ws, timeout=5.0)
                    if event["type"] == "session.updated":
                        break
            except TimeoutError:
                warnings.warn(
                    f"session.updated not received within {5.0}s after "
                    "session.update. The server may not implement this event.",
                    stacklevel=2,
                )

            # Start transcription
            await send_event(ws, {"type": "input_audio_buffer.commit"})

            for chunk in mary_had_lamb_audio_chunks:
                await send_event(
                    ws, {"type": "input_audio_buffer.append", "audio": chunk}
                )

            await send_event(ws, {"type": "input_audio_buffer.commit", "final": True})

            done_received = False
            while not done_received:
                event = await receive_event(ws, timeout=60.0)
                if event["type"] == "transcription.done":
                    done_received = True
                elif event["type"] == "error":
                    pytest.fail(f"Engine error after empty commit: {event}")
            assert done_received