async def process_vad_audio() -> None:
                nonlocal vad_audio_buffer
                last_speech_time = datetime.now(tz=timezone.utc)
                vad = get_vad()
                while True:
                    base64_data = await vad_queue.get()
                    raw_chunk_24k = base64.b64decode(base64_data)
                    vad_audio_buffer.extend(raw_chunk_24k)
                    has_speech = False
                    while len(vad_audio_buffer) >= BYTES_PER_24K_FRAME:
                        frame_24k = vad_audio_buffer[:BYTES_PER_24K_FRAME]
                        del vad_audio_buffer[:BYTES_PER_24K_FRAME]
                        try:
                            frame_16k = resample_24k_to_16k(frame_24k)
                            is_speech = vad.is_speech(frame_16k, VAD_SAMPLE_RATE_16K)
                            if is_speech:
                                has_speech = True
                                logger.trace("!", end="")
                                if bot_speaking_flag[0]:
                                    msg_handler.openai_send({"type": "response.cancel"})
                                    bot_speaking_flag[0] = False
                        except Exception as e:  # noqa: BLE001
                            await logger.aerror(f"[ERROR] VAD processing failed (ValueError): {e}")
                            continue
                    if has_speech:
                        last_speech_time = datetime.now(tz=timezone.utc)
                        logger.trace(".", end="")
                    else:
                        time_since_speech = (datetime.now(tz=timezone.utc) - last_speech_time).total_seconds()
                        if time_since_speech >= 1.0:
                            logger.trace("_", end="")