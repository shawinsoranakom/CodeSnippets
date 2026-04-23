async def forward_to_openai() -> None:
                nonlocal openai_realtime_session
                create_response = get_create_response(msg_handler, session_id)
                try:
                    num_audio_samples = 0  # Initialize as an integer instead of None
                    while True:
                        message_text = await client_websocket.receive_text()
                        msg = json.loads(message_text)
                        log_event(msg, CLIENT_TO_LF)
                        if msg.get("type") == "input_audio_buffer.append":
                            logger.trace(f"buffer_id {msg.get('buffer_id', '')}")
                            base64_data = msg.get("audio", "")
                            if not base64_data:
                                continue
                            # Ensure we're adding to an integer
                            num_audio_samples += len(base64_data)
                            event = {"type": "input_audio_buffer.append", "audio": base64_data}
                            msg_handler.openai_send(event)
                            if voice_config.barge_in_enabled:
                                await vad_queue.put(base64_data)
                        elif msg.get("type") == "response.create":
                            create_response(msg)
                        elif msg.get("type") == "input_audio_buffer.commit":
                            if num_audio_samples > AUDIO_SAMPLE_THRESHOLD:
                                msg_handler.openai_send(msg)
                                num_audio_samples = 0
                        elif msg.get("type") == "langflow.voice_mode.config":
                            await logger.ainfo(f"langflow.voice_mode.config {msg}")
                            voice_config.progress_enabled = msg.get("progress_enabled", True)
                        elif msg.get("type") == "langflow.elevenlabs.config":
                            await logger.ainfo(f"langflow.elevenlabs.config {msg}")
                            voice_config.use_elevenlabs = msg["enabled"]
                            voice_config.elevenlabs_voice = msg.get("voice_id", voice_config.elevenlabs_voice)

                            # Update modalities based on TTS choice
                            modalities = ["text"] if voice_config.use_elevenlabs else ["audio", "text"]
                            openai_realtime_session["modalities"] = modalities
                            session_update = {"type": "session.update", "session": openai_realtime_session}
                            msg_handler.openai_send(session_update)
                        elif msg.get("type") == "session.update":
                            openai_realtime_session = update_global_session(msg["session"])
                            session_update = {"type": "session.update", "session": openai_realtime_session}
                            msg_handler.openai_send(session_update)
                        else:
                            msg_handler.openai_send(msg)
                except (WebSocketDisconnect, websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
                    pass