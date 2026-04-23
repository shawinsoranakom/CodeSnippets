async def openai_stream_generator() -> AsyncGenerator[str, None]:
            """Convert Langflow events to OpenAI Responses API streaming format."""
            main_task = asyncio.create_task(
                run_flow_generator(
                    flow=flow,
                    input_request=simplified_request,
                    api_key_user=api_key_user,
                    event_manager=event_manager,
                    client_consumed_queue=asyncio_queue_client_consumed,
                    context=context,
                )
            )

            try:
                await logger.adebug(
                    "[OpenAIResponses][stream] start: response_id=%s model=%s session_id=%s",
                    response_id,
                    request.model,
                    session_id,
                )
                # Send initial chunk to establish connection
                initial_chunk = OpenAIResponsesStreamChunk(
                    id=response_id,
                    created=created_timestamp,
                    model=request.model,
                    delta={"content": ""},
                )
                yield f"data: {initial_chunk.model_dump_json()}\n\n"

                tool_call_counter = 0
                processed_tools = set()  # Track processed tool calls to avoid duplicates
                previous_content = ""  # Track content already sent to calculate deltas
                stream_usage_data = None  # Track usage from completed message

                async for event_data in consume_and_yield(asyncio_queue, asyncio_queue_client_consumed):
                    if event_data is None:
                        await logger.adebug("[OpenAIResponses][stream] received None event_data; breaking loop")
                        break

                    content = ""
                    token_data = {}

                    # Parse byte string events as JSON
                    if isinstance(event_data, bytes):
                        try:
                            import json

                            event_str = event_data.decode("utf-8")
                            parsed_event = json.loads(event_str)

                            if isinstance(parsed_event, dict):
                                event_type = parsed_event.get("event")
                                data = parsed_event.get("data", {})
                                await logger.adebug(
                                    "[OpenAIResponses][stream] event: %s keys=%s",
                                    event_type,
                                    list(data.keys()) if isinstance(data, dict) else type(data),
                                )

                                # Handle add_message events
                                if event_type == "token":
                                    token_data = data.get("chunk", "")
                                    await logger.adebug(
                                        "[OpenAIResponses][stream] token: token_data=%s",
                                        token_data,
                                    )
                                if event_type == "error":
                                    # Error message is in 'text' field, not 'error' field
                                    # The 'error' field is a boolean flag
                                    error_message = data.get("text") or data.get("error", "Unknown error")
                                    # Ensure error_message is a string
                                    if not isinstance(error_message, str):
                                        error_message = str(error_message)
                                    # Send error as content chunk with finish_reason="error"
                                    # This ensures OpenAI SDK can parse and surface the error
                                    error_chunk = create_openai_error_chunk(
                                        response_id=response_id,
                                        created_timestamp=created_timestamp,
                                        model=request.model,
                                        error_message=error_message,
                                    )
                                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                                    yield "data: [DONE]\n\n"
                                    # Exit early after error
                                    return

                                if event_type == "add_message":
                                    sender_name = data.get("sender_name", "")
                                    text = data.get("text", "")
                                    sender = data.get("sender", "")
                                    content_blocks = data.get("content_blocks", [])

                                    # Get message state from properties
                                    properties = data.get("properties", {})
                                    message_state = properties.get("state") if isinstance(properties, dict) else None

                                    await logger.adebug(
                                        (
                                            "[OpenAIResponses][stream] add_message: "
                                            "sender=%s sender_name=%s text_len=%d state=%s"
                                        ),
                                        sender,
                                        sender_name,
                                        len(text) if isinstance(text, str) else -1,
                                        message_state,
                                    )

                                    # Skip processing text content if state is "complete"
                                    # All content has already been streamed via token events
                                    if message_state == "complete":
                                        await logger.adebug(
                                            "[OpenAIResponses][stream] skipping add_message with state=complete"
                                        )
                                        # Extract usage from completed message properties
                                        if isinstance(properties, dict) and "usage" in properties:
                                            usage_obj = properties.get("usage")
                                            if usage_obj and isinstance(usage_obj, dict):
                                                # Convert None values to 0 for compatibility
                                                stream_usage_data = {
                                                    "input_tokens": usage_obj.get("input_tokens") or 0,
                                                    "output_tokens": usage_obj.get("output_tokens") or 0,
                                                    "total_tokens": usage_obj.get("total_tokens") or 0,
                                                }
                                                await logger.adebug(
                                                    "[OpenAIResponses][stream] captured usage: %s", stream_usage_data
                                                )
                                        # Still process content_blocks for tool calls, but skip text content
                                        text = ""

                                    # Look for Agent Steps in content_blocks
                                    for block in content_blocks:
                                        if block.get("title") == "Agent Steps":
                                            contents = block.get("contents", [])
                                            for step in contents:
                                                # Look for tool_use type items
                                                if step.get("type") == "tool_use":
                                                    tool_name = step.get("name", "")
                                                    tool_input = step.get("tool_input", {})
                                                    tool_output = step.get("output")

                                                    # Only emit tool calls with explicit tool names and
                                                    # meaningful arguments
                                                    if tool_name and tool_input is not None and tool_output is not None:
                                                        # Create unique identifier for this tool call
                                                        tool_signature = (
                                                            f"{tool_name}:{hash(str(sorted(tool_input.items())))}"
                                                        )

                                                        # Skip if we've already processed this tool call
                                                        if tool_signature in processed_tools:
                                                            continue

                                                        processed_tools.add(tool_signature)
                                                        tool_call_counter += 1
                                                        call_id = f"call_{tool_call_counter}"
                                                        tool_id = f"fc_{tool_call_counter}"
                                                        tool_call_event = {
                                                            "type": "response.output_item.added",
                                                            "item": {
                                                                "id": tool_id,
                                                                "type": "function_call",  # OpenAI uses "function_call"
                                                                "status": "in_progress",  # OpenAI includes status
                                                                "name": tool_name,
                                                                "arguments": "",  # Start with empty, build via deltas
                                                                "call_id": call_id,
                                                            },
                                                        }
                                                        yield (
                                                            f"event: response.output_item.added\n"
                                                            f"data: {json.dumps(tool_call_event)}\n\n"
                                                        )

                                                        # Send function call arguments as delta events (like OpenAI)
                                                        arguments_str = json.dumps(tool_input)
                                                        arg_delta_event = {
                                                            "type": "response.function_call_arguments.delta",
                                                            "delta": arguments_str,
                                                            "item_id": tool_id,
                                                            "output_index": 0,
                                                        }
                                                        yield (
                                                            f"event: response.function_call_arguments.delta\n"
                                                            f"data: {json.dumps(arg_delta_event)}\n\n"
                                                        )

                                                        # Send function call arguments done event
                                                        arg_done_event = {
                                                            "type": "response.function_call_arguments.done",
                                                            "arguments": arguments_str,
                                                            "item_id": tool_id,
                                                            "output_index": 0,
                                                        }
                                                        yield (
                                                            f"event: response.function_call_arguments.done\n"
                                                            f"data: {json.dumps(arg_done_event)}\n\n"
                                                        )
                                                        await logger.adebug(
                                                            "[OpenAIResponses][stream] tool_call.args.done name=%s",
                                                            tool_name,
                                                        )

                                                        # If there's output, send completion event
                                                        if tool_output is not None:
                                                            # Check if include parameter requests tool_call.results
                                                            include_results = (
                                                                request.include
                                                                and "tool_call.results" in request.include
                                                            )

                                                            if include_results:
                                                                # Format with detailed results
                                                                tool_done_event = {
                                                                    "type": "response.output_item.done",
                                                                    "item": {
                                                                        "id": f"{tool_name}_{tool_id}",
                                                                        "inputs": tool_input,  # Raw inputs as-is
                                                                        "status": "completed",
                                                                        "type": "tool_call",
                                                                        "tool_name": f"{tool_name}",
                                                                        "results": tool_output,  # Raw output as-is
                                                                    },
                                                                    "output_index": 0,
                                                                    "sequence_number": tool_call_counter + 5,
                                                                }
                                                            else:
                                                                # Regular function call format
                                                                tool_done_event = {
                                                                    "type": "response.output_item.done",
                                                                    "item": {
                                                                        "id": tool_id,
                                                                        "type": "function_call",  # Match OpenAI format
                                                                        "status": "completed",
                                                                        "arguments": arguments_str,
                                                                        "call_id": call_id,
                                                                        "name": tool_name,
                                                                    },
                                                                }

                                                            yield (
                                                                f"event: response.output_item.done\n"
                                                                f"data: {json.dumps(tool_done_event)}\n\n"
                                                            )
                                                            await logger.adebug(
                                                                "[OpenAIResponses][stream] tool_call.done name=%s",
                                                                tool_name,
                                                            )

                                    # Extract text content for streaming (only AI responses)
                                    if (
                                        sender in ["Machine", "AI", "Agent"]
                                        and text != request.input
                                        and sender_name in ["Agent", "AI"]
                                    ):
                                        # Calculate delta: only send newly generated content
                                        if text.startswith(previous_content):
                                            content = text[len(previous_content) :]
                                            previous_content = text
                                            await logger.adebug(
                                                "[OpenAIResponses][stream] delta computed len=%d total_len=%d",
                                                len(content),
                                                len(previous_content),
                                            )
                                        else:
                                            # If text doesn't start with previous content, send full text
                                            # This handles cases where the content might be reset
                                            content = text
                                            previous_content = text
                                            await logger.adebug(
                                                "[OpenAIResponses][stream] content reset; sending full text len=%d",
                                                len(content),
                                            )

                        except (json.JSONDecodeError, UnicodeDecodeError):
                            await logger.adebug("[OpenAIResponses][stream] failed to decode event bytes; skipping")
                            continue

                    # Only send chunks with actual content
                    if content or token_data:
                        if isinstance(token_data, str):
                            content = token_data
                            await logger.adebug(
                                f"[OpenAIResponses][stream] sent chunk with content={content}",
                            )
                        chunk = OpenAIResponsesStreamChunk(
                            id=response_id,
                            created=created_timestamp,
                            model=request.model,
                            delta={"content": content},
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"
                        await logger.adebug(
                            "[OpenAIResponses][stream] sent chunk with delta_len=%d",
                            len(content),
                        )

                # Send final completion chunk
                final_chunk = OpenAIResponsesStreamChunk(
                    id=response_id,
                    created=created_timestamp,
                    model=request.model,
                    delta={},
                    status="completed",
                    finish_reason="stop",
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"

                # Send response.completed event with usage (OpenAI format)
                completed_event = {
                    "type": "response.completed",
                    "response": {
                        "id": response_id,
                        "object": "response",
                        "created_at": created_timestamp,
                        "status": "completed",
                        "model": request.model,
                        "usage": stream_usage_data,
                    },
                }
                yield f"event: response.completed\ndata: {json.dumps(completed_event)}\n\n"

                yield "data: [DONE]\n\n"
                await logger.adebug(
                    "[OpenAIResponses][stream] completed: response_id=%s total_sent_len=%d usage=%s",
                    response_id,
                    len(previous_content),
                    stream_usage_data,
                )

            except Exception as e:  # noqa: BLE001
                logger.error(f"Error in stream generator: {e}")
                # Send error as content chunk with finish_reason="error"
                error_chunk = create_openai_error_chunk(
                    response_id=response_id,
                    created_timestamp=created_timestamp,
                    model=request.model,
                    error_message=str(e),
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                if not main_task.done():
                    main_task.cancel()