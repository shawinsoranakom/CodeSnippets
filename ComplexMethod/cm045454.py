async def _reflect_on_tool_use_flow(
        cls,
        system_messages: List[SystemMessage],
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        model_context: ChatCompletionContext,
        workbench: Sequence[Workbench],
        handoff_tools: List[BaseTool[Any, Any]],
        agent_name: str,
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
        output_content_type: type[BaseModel] | None,
        cancellation_token: CancellationToken,
    ) -> AsyncGenerator[Response | ModelClientStreamingChunkEvent | ThoughtEvent, None]:
        """
        If reflect_on_tool_use=True, we do another inference based on tool results
        and yield the final text response (or streaming chunks).
        """
        all_messages = system_messages + await model_context.get_messages()
        llm_messages = cls._get_compatible_context(model_client=model_client, messages=all_messages)

        reflection_result: Optional[CreateResult] = None

        # Generate a message ID for correlation between chunks and final message in reflection flow
        reflection_message_id = str(uuid.uuid4())

        if model_client_stream:
            async for chunk in model_client.create_stream(
                llm_messages,
                json_output=output_content_type,
                cancellation_token=cancellation_token,
                tool_choice="none",  # Do not use tools in reflection flow.
            ):
                if isinstance(chunk, CreateResult):
                    reflection_result = chunk
                elif isinstance(chunk, str):
                    yield ModelClientStreamingChunkEvent(
                        content=chunk, source=agent_name, full_message_id=reflection_message_id
                    )
                else:
                    raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
        else:
            reflection_result = await model_client.create(
                llm_messages,
                json_output=output_content_type,
                cancellation_token=cancellation_token,
                tool_choice="none",  # Do not use tools in reflection flow.
            )

        if not reflection_result or not isinstance(reflection_result.content, str):
            raise RuntimeError("Reflect on tool use produced no valid text response.")

        # --- NEW: If the reflection produced a thought, yield it ---
        if reflection_result.thought:
            thought_event = ThoughtEvent(content=reflection_result.thought, source=agent_name)
            yield thought_event
            inner_messages.append(thought_event)

        # Add to context (including thought if present)
        await model_context.add_message(
            AssistantMessage(
                content=reflection_result.content,
                source=agent_name,
                thought=getattr(reflection_result, "thought", None),
            )
        )

        if output_content_type:
            content = output_content_type.model_validate_json(reflection_result.content)
            yield Response(
                chat_message=StructuredMessage[output_content_type](  # type: ignore[valid-type]
                    content=content,
                    source=agent_name,
                    models_usage=reflection_result.usage,
                    id=reflection_message_id,
                ),
                inner_messages=inner_messages,
            )
        else:
            yield Response(
                chat_message=TextMessage(
                    content=reflection_result.content,
                    source=agent_name,
                    models_usage=reflection_result.usage,
                    id=reflection_message_id,
                ),
                inner_messages=inner_messages,
            )