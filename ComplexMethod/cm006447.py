async def flow_as_tool_websocket(
    client_websocket: WebSocket,
    flow_id: str,
    background_tasks: BackgroundTasks,
    session: DbSession,
    session_id: str,
):
    """WebSocket endpoint registering the flow as a tool for real-time interaction."""
    try:
        await client_websocket.accept()

        log_event = create_event_logger()

        vad_task: asyncio.Task | None = None
        voice_config = get_voice_config(session_id)
        current_user: User = await get_current_user_for_websocket(client_websocket, session)
        current_user, openai_key = await authenticate_and_get_openai_key(session, current_user, client_websocket)
        if current_user is None or openai_key is None:
            return
        try:
            flow_description = await get_flow_desc_from_db(flow_id)
            flow_tool = {
                "name": "execute_flow",
                "type": "function",
                "description": flow_description or "Execute the flow with the given input",
                "parameters": {
                    "type": "object",
                    "properties": {"input": {"type": "string", "description": "The input to send to the flow"}},
                    "required": ["input"],
                },
            }
        except Exception as e:  # noqa: BLE001
            err_msg = {"error": f"Failed to load flow: {e!s}"}
            await client_websocket.send_json(err_msg)
            await logger.aerror(f"Failed to load flow: {e}")
            return

        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        def init_session_dict():
            session_dict = voice_config.get_session_dict()
            session_dict["tools"] = [flow_tool]
            return session_dict

        async with websockets.connect(url, extra_headers=headers) as openai_ws:
            msg_handler = SendQueues(openai_ws, client_websocket, log_event)

            openai_realtime_session = init_session_dict()

            session_update = {"type": "session.update", "session": openai_realtime_session}
            msg_handler.openai_send(session_update)

            # Setup for VAD processing.
            vad_queue: asyncio.Queue = asyncio.Queue()
            vad_audio_buffer = bytearray()
            bot_speaking_flag = [False]

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

            def client_send_event_from_thread(event, loop) -> None:
                return loop.call_soon_threadsafe(msg_handler.client_send, event)

            def pass_through(from_dict, to_dict, keys):
                for key in keys:
                    if key in from_dict:
                        to_dict[key] = from_dict[key]

            def merge(from_dict, to_dict, keys):
                for key in keys:
                    if key in from_dict:
                        if not isinstance(from_dict[key], str):
                            msg = f"Only string values are supported for merge. Issue with key: {key}"
                            raise ValueError(msg)
                        new_value = from_dict[key]

                        if key not in to_dict:
                            to_dict[key] = new_value
                        else:
                            if not isinstance(to_dict[key], str):
                                msg = f"Only string values are supported for merge. Issue with key: {key}"
                                raise ValueError(msg)
                            old_value = to_dict[key]

                            to_dict[key] = f"{old_value}\n{new_value}"

            def warn_if_present(config_dict, keys):
                for key in keys:
                    if key in config_dict:
                        logger.warning(f"Removing key {key} from session.update.")

            def update_global_session(from_session):
                # Create a new session dict instead of modifying global
                new_session = init_session_dict()
                pass_through(
                    from_session,
                    new_session,
                    ["voice", "temperature", "turn_detection", "input_audio_transcription"],
                )
                merge(from_session, new_session, ["instructions"])
                warn_if_present(
                    from_session, ["modalities", "tools", "tool_choice", "input_audio_format", "output_audio_format"]
                )
                return new_session

            class Response:
                def __init__(self, response_id: str, *, use_elevenlabs: bool | None = None):
                    if use_elevenlabs is None:
                        use_elevenlabs = False
                    self.response_id = response_id
                    if use_elevenlabs:
                        self.text_delta_queue: asyncio.Queue = asyncio.Queue()
                        self.text_delta_task = asyncio.create_task(process_text_deltas(self))

            responses = {}

            async def process_text_deltas(rsp: Response):
                """Transfer text deltas from the async queue to a synchronous queue.

                then run the ElevenLabs TTS call (which expects a sync generator) in a separate thread.
                """
                try:
                    elevenlabs_client = await get_or_create_elevenlabs_client(current_user.id, session)
                    if elevenlabs_client is None:
                        return

                    async def get_chunks(q: asyncio.Queue):
                        delims = [".", "?", ";", "!"]
                        buf: str = ""
                        while True:
                            text = await q.get()
                            if text is None:
                                if len(buf) > 0:
                                    yield buf
                                return
                            buf += text
                            delim_locs = []
                            for delim in delims:
                                i = buf.find(delim)
                                while i != -1:
                                    delim_locs.append(i)
                                    i = buf.find(delim, i + 1)
                            substr_begin = 0
                            for delim_loc in delim_locs:
                                chunk = buf[substr_begin : delim_loc + 1]
                                substr_begin = delim_loc + 1
                                yield chunk
                            buf = buf[substr_begin:]

                    chunk_gen = get_chunks(rsp.text_delta_queue)

                    async for text_chunk in chunk_gen:
                        audio_chunks = elevenlabs_client.generate(
                            voice=voice_config.elevenlabs_voice,
                            output_format="pcm_24000",
                            text=text_chunk,  # synchronous generator expected by ElevenLabs
                            model=voice_config.elevenlabs_model,
                            voice_settings=None,
                            stream=True,
                        )
                        for audio_chunk in audio_chunks:
                            base64_audio = base64.b64encode(audio_chunk).decode("utf-8")
                            # Schedule sending the audio chunk in the main event loop.
                            event = {
                                "type": "response.audio.delta",
                                "delta": base64_audio,
                                "response_id": rsp.response_id,
                            }
                            # client_send_event_from_thread(event, main_loop)
                            msg_handler.client_send(event)

                    event = {"type": "response.audio.done", "response_id": rsp.response_id}
                    # client_send_event_from_thread(event, main_loop)
                    msg_handler.client_send(event)
                except Exception:  # noqa: BLE001
                    await logger.aerror(traceback.format_exc())

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

            async def forward_to_client() -> None:
                nonlocal bot_speaking_flag, responses
                conversation_id = str(uuid4())
                function_call = None
                rsp: Response | None = None
                # Store function call tasks to prevent garbage collection

                try:
                    while True:
                        data = await openai_ws.recv()
                        event = json.loads(data)
                        log_event(event, OPENAI_TO_LF)
                        event_type = event.get("type")
                        response_id = event.get("response_id", None) or event.get("response", {}).get("id", None)

                        do_forward = True
                        do_forward = do_forward and not (event_type == "response.done" and voice_config.use_elevenlabs)
                        do_forward = do_forward and event_type.find("flow.") != 0

                        if do_forward:
                            msg_handler.client_send(event)
                        if event_type == "response.created":
                            responses[response_id] = Response(response_id, use_elevenlabs=voice_config.use_elevenlabs)
                            if function_call:
                                if function_call.is_prog_enabled and not function_call.prog_rsp_id:
                                    function_call.prog_rsp_id = response_id
                                elif not function_call.func_rsp_id:
                                    function_call.func_rsp_id = response_id
                        elif event_type == "response.text.delta":
                            rsp = responses[response_id]
                            if voice_config.use_elevenlabs:
                                delta = event.get("delta", "")
                                await rsp.text_delta_queue.put(delta)
                        elif event_type == "response.text.done":
                            rsp = responses[response_id]
                            if voice_config.use_elevenlabs:
                                await rsp.text_delta_queue.put(None)
                                if rsp.text_delta_task and not rsp.text_delta_task.done():
                                    await rsp.text_delta_task
                                responses.pop(response_id)
                                msg_handler.client_send({"type": "response.done", "response": {"id": response_id}})

                                try:
                                    message_text = event.get("text", "")
                                    await add_message_to_db(message_text, session, flow_id, session_id, "Machine", "AI")
                                except ValueError as err:
                                    await logger.aerror(f"Error saving message to database (ValueError): {err}")
                                    await logger.aerror(traceback.format_exc())
                                except (KeyError, AttributeError, TypeError) as err:
                                    # Replace blind Exception with specific exceptions
                                    await logger.aerror(f"Error saving message to database: {err}")
                                    await logger.aerror(traceback.format_exc())

                        elif event_type == "response.output_item.added":
                            bot_speaking_flag[0] = True
                            item = event.get("item", {})
                            if item.get("type") == "function_call" and (
                                not function_call or (function_call and function_call.done)
                            ):
                                function_call = FunctionCall(
                                    item=item,
                                    msg_handler=msg_handler,
                                    flow_id=flow_id,
                                    background_tasks=background_tasks,
                                    current_user=current_user,
                                    conversation_id=conversation_id,
                                    session_id=session_id,
                                    is_prog_enabled=voice_config.progress_enabled,
                                )
                        elif event_type == "response.output_item.done":
                            try:
                                transcript = extract_transcript(event)
                                if transcript and transcript.strip():
                                    await add_message_to_db(transcript, session, flow_id, session_id, "Machine", "AI")
                            except ValueError as err:
                                await logger.aerror(f"Error saving message to database (ValueError): {err}")
                                await logger.aerror(traceback.format_exc())
                            except (KeyError, AttributeError, TypeError) as err:
                                # Replace blind Exception with specific exceptions
                                await logger.aerror(f"Error saving message to database: {err}")
                                await logger.aerror(traceback.format_exc())
                            bot_speaking_flag[0] = False
                        elif event_type == "response.done":
                            msg_handler.openai_unblock()
                        elif event_type == "response.function_call_arguments.delta":
                            if function_call and response_id not in (
                                function_call.prog_rsp_id,
                                function_call.func_rsp_id,
                            ):
                                function_call.append_args(event.get("delta", ""))
                        elif event_type == "response.function_call_arguments.done":
                            if function_call and response_id not in (
                                function_call.prog_rsp_id,
                                function_call.func_rsp_id,
                            ):
                                function_call.execute()
                        elif event_type == "response.audio.delta":
                            # there are no audio deltas from OpenAI if ElevenLabs is used (because modality = ["text"]).
                            event.get("delta", "")
                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            try:
                                message_text = event.get("transcript", "")
                                if message_text and message_text.strip():
                                    await add_message_to_db(message_text, session, flow_id, session_id, "User", "User")
                            except ValueError as e:
                                await logger.aerror(f"Error saving message to database (ValueError): {e}")
                                await logger.aerror(traceback.format_exc())
                            except (KeyError, AttributeError, TypeError) as e:
                                # Replace blind Exception with specific exceptions
                                await logger.aerror(f"Error saving message to database: {e}")
                                await logger.aerror(traceback.format_exc())
                        elif event_type == "error":
                            pass

                except (WebSocketDisconnect, websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
                    pass

            if voice_config.barge_in_enabled:
                # Store the task reference to prevent it from being garbage collected
                vad_task = asyncio.create_task(process_vad_audio())

            try:
                # Use gather with return_exceptions to collect any exceptions
                tasks = [asyncio.create_task(forward_to_openai()), asyncio.create_task(forward_to_client())]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for exceptions in results
                for result in results:
                    if isinstance(result, Exception):
                        await logger.aerror("WS loop failed:", exc_info=result)
                        await logger.aerror(traceback.format_exc())
            except Exception as e:  # noqa: BLE001
                # Handle any other exceptions
                await logger.aerror(f"WS loop failed: {e}")
                await logger.aerror(traceback.format_exc())
            finally:
                # shared cleanup for writers & sockets
                async def close():
                    await msg_handler.close()
                    await client_websocket.close()
                    await openai_ws.close()

                await close()
    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Unexpected error: {e}")
        await logger.aerror(traceback.format_exc())
    finally:
        # Make sure to clean up the task
        if vad_task and not vad_task.done():
            vad_task.cancel()