async def test_multi_chunk_streaming(
    model_name, mary_had_lamb_audio_chunks, rocm_aiter_fa_attention
):
    """Test streaming multiple audio chunks before committing."""
    server_args = ["--enforce-eager", "--max-model-len", "2048"]

    if model_name.startswith("mistralai"):
        server_args += MISTRAL_FORMAT_ARGS

    add_attention_backend(server_args, rocm_aiter_fa_attention)

    with RemoteOpenAIServer(
        model_name, server_args, env_dict=REALTIME_ENV_OVERRIDES
    ) as remote_server:
        ws_url = _get_websocket_url(remote_server)
        async with websockets.connect(ws_url) as ws:
            # Receive session.created
            event = await receive_event(ws, timeout=30.0)
            assert event["type"] == "session.created"

            await send_event(ws, {"type": "session.update", "model": model_name})

            # Wait for the server to acknowledge the session update.
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

            # (ROCm) Warm-up: send a non-final commit (required to start
            # transcription) with a small audio chunk to trigger aiter
            # compilation on first use.
            await send_event(ws, {"type": "input_audio_buffer.commit"})
            await send_event(
                ws,
                {
                    "type": "input_audio_buffer.append",
                    "audio": mary_had_lamb_audio_chunks[0],
                },
            )
            await send_event(ws, {"type": "input_audio_buffer.commit", "final": True})

            # (ROCm) Drain all warm-up responses with generous timeout for
            # JIT compilation
            warmup_done = False
            while not warmup_done:
                event = await receive_event(ws, timeout=600.0)
                if event["type"] in ("transcription.done", "error"):
                    warmup_done = True

            # Now send the real test audio
            await send_event(ws, {"type": "input_audio_buffer.commit"})

            # Send multiple audio chunks
            for chunk in mary_had_lamb_audio_chunks:
                await send_event(
                    ws, {"type": "input_audio_buffer.append", "audio": chunk}
                )

            # Send commit to end
            await send_event(ws, {"type": "input_audio_buffer.commit", "final": True})

            # Collect transcription deltas
            full_text = ""
            done_received = False

            while not done_received:
                event = await receive_event(ws, timeout=60.0)

                if event["type"] == "transcription.delta":
                    full_text += event["delta"]
                elif event["type"] == "transcription.done":
                    done_received = True
                    assert "text" in event
                elif event["type"] == "error":
                    pytest.fail(f"Received error: {event}")

            # Verify transcription contains expected content
            assert event["type"] == "transcription.done"
            assert event["text"] == full_text
            assert full_text == (
                " First words I spoke in the original phonograph."
                " A little piece of practical poetry. Mary had a little lamb,"
                " it sleeps with quite a flow, and everywhere that Mary went,"
                " the lamb was sure to go."
            )