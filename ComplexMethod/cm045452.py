async def _process_model_result(
        cls,
        model_result: CreateResult,
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
        cancellation_token: CancellationToken,
        agent_name: str,
        system_messages: List[SystemMessage],
        model_context: ChatCompletionContext,
        workbench: Sequence[Workbench],
        handoff_tools: List[BaseTool[Any, Any]],
        handoffs: Dict[str, HandoffBase],
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        reflect_on_tool_use: bool,
        tool_call_summary_format: str,
        tool_call_summary_formatter: Callable[[FunctionCall, FunctionExecutionResult], str] | None,
        max_tool_iterations: int,
        output_content_type: type[BaseModel] | None,
        message_id: str,
        format_string: str | None = None,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """
        Handle final or partial responses from model_result, including tool calls, handoffs,
        and reflection if needed. Supports tool call loops when enabled.
        """

        # Tool call loop implementation with streaming support
        current_model_result = model_result
        # This variable is needed for the final summary/reflection step
        executed_calls_and_results: List[Tuple[FunctionCall, FunctionExecutionResult]] = []

        for loop_iteration in range(max_tool_iterations):
            # If direct text response (string), we're done
            if isinstance(current_model_result.content, str):
                # Use the passed message ID for the final message
                if output_content_type:
                    content = output_content_type.model_validate_json(current_model_result.content)
                    yield Response(
                        chat_message=StructuredMessage[output_content_type](  # type: ignore[valid-type]
                            content=content,
                            source=agent_name,
                            models_usage=current_model_result.usage,
                            format_string=format_string,
                            id=message_id,
                        ),
                        inner_messages=inner_messages,
                    )
                else:
                    yield Response(
                        chat_message=TextMessage(
                            content=current_model_result.content,
                            source=agent_name,
                            models_usage=current_model_result.usage,
                            id=message_id,
                        ),
                        inner_messages=inner_messages,
                    )
                return

            # Otherwise, we have function calls
            assert isinstance(current_model_result.content, list) and all(
                isinstance(item, FunctionCall) for item in current_model_result.content
            )

            # STEP 4A: Yield ToolCallRequestEvent
            tool_call_msg = ToolCallRequestEvent(
                content=current_model_result.content,
                source=agent_name,
                models_usage=current_model_result.usage,
            )
            event_logger.debug(tool_call_msg)
            inner_messages.append(tool_call_msg)
            yield tool_call_msg

            # STEP 4B: Execute tool calls with streaming support
            # Use a queue to handle streaming results from tool calls.
            stream = asyncio.Queue[BaseAgentEvent | BaseChatMessage | None]()

            async def _execute_tool_calls(
                function_calls: List[FunctionCall],
                stream_queue: asyncio.Queue[BaseAgentEvent | BaseChatMessage | None],
            ) -> List[Tuple[FunctionCall, FunctionExecutionResult]]:
                results = await asyncio.gather(
                    *[
                        cls._execute_tool_call(
                            tool_call=call,
                            workbench=workbench,
                            handoff_tools=handoff_tools,
                            agent_name=agent_name,
                            cancellation_token=cancellation_token,
                            stream=stream_queue,
                        )
                        for call in function_calls
                    ]
                )
                # Signal the end of streaming by putting None in the queue.
                stream_queue.put_nowait(None)
                return results

            task = asyncio.create_task(_execute_tool_calls(current_model_result.content, stream))

            while True:
                event = await stream.get()
                if event is None:
                    # End of streaming, break the loop.
                    break
                if isinstance(event, BaseAgentEvent) or isinstance(event, BaseChatMessage):
                    yield event
                    inner_messages.append(event)
                else:
                    raise RuntimeError(f"Unexpected event type: {type(event)}")

            # Wait for all tool calls to complete.
            executed_calls_and_results = await task
            exec_results = [result for _, result in executed_calls_and_results]

            # Yield ToolCallExecutionEvent
            tool_call_result_msg = ToolCallExecutionEvent(
                content=exec_results,
                source=agent_name,
            )
            event_logger.debug(tool_call_result_msg)
            await model_context.add_message(FunctionExecutionResultMessage(content=exec_results))
            inner_messages.append(tool_call_result_msg)
            yield tool_call_result_msg

            # STEP 4C: Check for handoff
            handoff_output = cls._check_and_handle_handoff(
                model_result=current_model_result,
                executed_calls_and_results=executed_calls_and_results,
                inner_messages=inner_messages,
                handoffs=handoffs,
                agent_name=agent_name,
            )
            if handoff_output:
                yield handoff_output
                return

            # STEP 4D: Check if we should continue the loop.
            # If we are on the last iteration, break to the summary/reflection step.
            if loop_iteration == max_tool_iterations - 1:
                break

            # Continue the loop: make another model call using _call_llm
            next_model_result: Optional[CreateResult] = None
            async for llm_output in cls._call_llm(
                model_client=model_client,
                model_client_stream=model_client_stream,
                system_messages=system_messages,
                model_context=model_context,
                workbench=workbench,
                handoff_tools=handoff_tools,
                agent_name=agent_name,
                cancellation_token=cancellation_token,
                output_content_type=output_content_type,
                message_id=message_id,  # Use same message ID for consistency
            ):
                if isinstance(llm_output, CreateResult):
                    next_model_result = llm_output
                else:
                    # Streaming chunk event
                    yield llm_output

            assert next_model_result is not None, "No model result was produced in tool call loop."
            current_model_result = next_model_result

            # Yield thought event if present
            if current_model_result.thought:
                thought_event = ThoughtEvent(content=current_model_result.thought, source=agent_name, id=message_id)
                yield thought_event
                inner_messages.append(thought_event)
                # Regenerate the message ID for correlation between streaming chunks and final message
                message_id = str(uuid.uuid4())

            # Add the assistant message to the model context (including thought if present)
            await model_context.add_message(
                AssistantMessage(
                    content=current_model_result.content,
                    source=agent_name,
                    thought=getattr(current_model_result, "thought", None),
                )
            )

        # After the loop, reflect or summarize tool results
        if reflect_on_tool_use:
            async for reflection_response in cls._reflect_on_tool_use_flow(
                system_messages=system_messages,
                model_client=model_client,
                model_client_stream=model_client_stream,
                model_context=model_context,
                workbench=workbench,
                handoff_tools=handoff_tools,
                agent_name=agent_name,
                inner_messages=inner_messages,
                output_content_type=output_content_type,
                cancellation_token=cancellation_token,
            ):
                yield reflection_response
        else:
            yield cls._summarize_tool_use(
                executed_calls_and_results=executed_calls_and_results,
                inner_messages=inner_messages,
                handoffs=handoffs,
                tool_call_summary_format=tool_call_summary_format,
                tool_call_summary_formatter=tool_call_summary_formatter,
                agent_name=agent_name,
            )
        return