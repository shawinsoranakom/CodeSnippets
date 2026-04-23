async def forward_to_client() -> None:
                try:
                    while True:
                        data = await openai_ws.recv()
                        event = json.loads(data)
                        client_send(event)
                        if event.get("type") == "conversation.item.input_audio_transcription.completed":
                            transcript = event.get("transcript")
                            if transcript is not None and transcript != "":
                                input_request = InputValueRequest(
                                    input_value=transcript, components=[], type="chat", session=session_id
                                )
                                response = await build_flow_and_stream(
                                    flow_id=UUID(flow_id),
                                    inputs=input_request,
                                    background_tasks=background_tasks,
                                    current_user=current_user,
                                )
                                result = ""
                                async for line in response.body_iterator:
                                    if not line:
                                        continue
                                    event_data = json.loads(line)
                                    client_send({"type": "flow.build.progress", "data": event_data})
                                    if event_data.get("event") == "end_vertex":
                                        text = (
                                            event_data.get("data", {})
                                            .get("build_data", "")
                                            .get("data", {})
                                            .get("results", {})
                                            .get("message", {})
                                            .get("text", "")
                                        )
                                        if text:
                                            result = text
                                if result != "":
                                    if tts_config.use_elevenlabs:
                                        elevenlabs_client = await get_or_create_elevenlabs_client(
                                            current_user.id, session
                                        )
                                        if elevenlabs_client is None:
                                            return
                                        audio_stream = elevenlabs_client.generate(
                                            voice=tts_config.elevenlabs_voice,
                                            output_format="pcm_24000",
                                            text=result,
                                            model=tts_config.elevenlabs_model,
                                            voice_settings=None,
                                            stream=True,
                                        )
                                        for chunk in audio_stream:
                                            base64_audio = base64.b64encode(chunk).decode("utf-8")
                                            audio_event = {"type": "response.audio.delta", "delta": base64_audio}
                                            client_send(audio_event)
                                    else:
                                        oai_client = tts_config.get_openai_client()
                                        voice = tts_config.get_openai_voice()
                                        response = oai_client.audio.speech.create(
                                            model="gpt-4o-mini-tts",
                                            voice=voice,
                                            input=result,  # Use result instead of undefined input variable
                                            instructions="be cheerful",
                                            response_format="pcm",
                                        )

                                        base64_audio = base64.b64encode(response.content).decode("utf-8")
                                        audio_event = {"type": "response.audio.delta", "delta": base64_audio}
                                        client_send(audio_event)
                except Exception as e:  # noqa: BLE001
                    await logger.aerror(f"Error in WebSocket communication: {e}")