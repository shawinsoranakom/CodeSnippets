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