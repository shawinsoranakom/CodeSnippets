async def forward_to_openai() -> None:
                try:
                    while True:
                        message_text = await client_websocket.receive_text()
                        event = json.loads(message_text)
                        if event.get("type") == "input_audio_buffer.append":
                            base64_data = event.get("audio", "")
                            if not base64_data:
                                continue
                            out_event = {"type": "input_audio_buffer.append", "audio": base64_data}
                            openai_send(out_event)
                        elif event.get("type") == "input_audio_buffer.commit":
                            openai_send(event)
                        elif event.get("type") == "langflow.elevenlabs.config":
                            await logger.ainfo(f"langflow.elevenlabs.config {event}")
                            tts_config.use_elevenlabs = event["enabled"]
                            tts_config.elevenlabs_voice = event.get("voice_id", tts_config.elevenlabs_voice)
                        elif event.get("type") == "voice.settings":
                            # Store the voice setting
                            if event.get("voice"):
                                tts_config.openai_voice = event.get("voice")
                                await logger.ainfo(f"Updated OpenAI voice to: {tts_config.openai_voice}")
                except Exception as e:  # noqa: BLE001
                    await logger.aerror(f"Error in WebSocket communication: {e}")