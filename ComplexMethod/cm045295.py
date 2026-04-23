async def RichConsole(
    stream: AsyncGenerator[BaseAgentEvent | BaseChatMessage | T, None],
    *,
    no_inline_images: bool = False,
    output_stats: bool = False,
    user_input_manager: UserInputManager | None = None,
) -> T:
    """
    Consumes the message stream from :meth:`~autogen_agentchat.base.TaskRunner.run_stream`
    or :meth:`~autogen_agentchat.base.ChatAgent.on_messages_stream` and renders the messages to the console.
    Returns the last processed TaskResult or Response.

    .. note::

        `output_stats` is experimental and the stats may not be accurate.
        It will be improved in future releases.

    Args:
        stream (AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None] | AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]): Message stream to render.
            This can be from :meth:`~autogen_agentchat.base.TaskRunner.run_stream` or :meth:`~autogen_agentchat.base.ChatAgent.on_messages_stream`.
        no_inline_images (bool, optional): If terminal is iTerm2 will render images inline. Use this to disable this behavior. Defaults to False.
        output_stats (bool, optional): (Experimental) If True, will output a summary of the messages and inline token usage info. Defaults to False.

    Returns:
        last_processed: A :class:`~autogen_agentchat.base.TaskResult` if the stream is from :meth:`~autogen_agentchat.base.TaskRunner.run_stream`
            or a :class:`~autogen_agentchat.base.Response` if the stream is from :meth:`~autogen_agentchat.base.ChatAgent.on_messages_stream`.
    """
    render_image_iterm = _is_running_in_iterm() and _is_output_a_tty() and not no_inline_images
    start_time = time.time()
    total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
    rich_console = Console()

    last_processed: Optional[T] = None

    async for message in stream:
        if isinstance(message, TaskResult):
            duration = time.time() - start_time
            if output_stats:
                output = (
                    f"Number of messages: {len(message.messages)}\n"
                    f"Finish reason: {message.stop_reason}\n"
                    f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                    f"Total completion tokens: {total_usage.completion_tokens}\n"
                    f"Duration: {duration:.2f} seconds\n"
                )
                await _aprint_panel(rich_console, output, "Summary")

            last_processed = message  # type: ignore

        elif isinstance(message, Response):
            duration = time.time() - start_time

            # Print final response.
            text_parts, image_parts = _extract_message_content(message.chat_message)
            if message.chat_message.models_usage:
                if output_stats:
                    text_parts.append(
                        f"[Prompt tokens: {message.chat_message.models_usage.prompt_tokens}, Completion tokens: {message.chat_message.models_usage.completion_tokens}]"
                    )
                total_usage.completion_tokens += message.chat_message.models_usage.completion_tokens
                total_usage.prompt_tokens += message.chat_message.models_usage.prompt_tokens

            await _aprint_message_content(
                rich_console,
                text_parts,
                image_parts,
                message.chat_message.source,
                render_image_iterm=render_image_iterm,
            )

            # Print summary.
            if output_stats:
                num_inner_messages = len(message.inner_messages) if message.inner_messages is not None else 0
                output = (
                    f"Number of inner messages: {num_inner_messages}\n"
                    f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                    f"Total completion tokens: {total_usage.completion_tokens}\n"
                    f"Duration: {duration:.2f} seconds\n"
                )
                await _aprint_panel(rich_console, output, "Summary")

            # mypy ignore
            last_processed = message  # type: ignore
        # We don't want to print UserInputRequestedEvent messages, we just use them to signal the user input event.
        elif isinstance(message, UserInputRequestedEvent):
            if user_input_manager is not None:
                user_input_manager.notify_event_received(message.request_id)
        elif isinstance(message, ModelClientStreamingChunkEvent):
            # TODO: Handle model client streaming chunk events.
            pass
        else:
            # Cast required for mypy to be happy
            message = cast(BaseAgentEvent | BaseChatMessage, message)  # type: ignore

            text_parts, image_parts = _extract_message_content(message)
            # Add usage stats if needed
            if message.models_usage:
                if output_stats:
                    text_parts.append(
                        f"[Prompt tokens: {message.models_usage.prompt_tokens}, Completion tokens: {message.models_usage.completion_tokens}]"
                    )
                total_usage.completion_tokens += message.models_usage.completion_tokens
                total_usage.prompt_tokens += message.models_usage.prompt_tokens

            await _aprint_message_content(
                rich_console,
                text_parts,
                image_parts,
                message.source,
                render_image_iterm=render_image_iterm,
            )

    if last_processed is None:
        raise ValueError("No TaskResult or Response was processed.")

    return last_processed