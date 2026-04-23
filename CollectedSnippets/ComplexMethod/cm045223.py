async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """Handle incoming messages and return a response."""
        await self._ensure_initialized()

        # Process all messages in sequence
        for message in messages:
            await self.handle_incoming_message(message, cancellation_token)

        # Inner messages for tool calls
        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []

        # Create and start a run
        run: Run = await cancellation_token.link_future(
            asyncio.ensure_future(
                self._client.beta.threads.runs.create(  # type: ignore[reportDeprecated]
                    thread_id=self._thread_id,
                    assistant_id=self._get_assistant_id,
                )
            )
        )

        # Wait for run completion by polling
        while True:
            run = await cancellation_token.link_future(
                asyncio.ensure_future(
                    self._client.beta.threads.runs.retrieve(  # type: ignore[reportDeprecated]
                        thread_id=self._thread_id,
                        run_id=run.id,
                    )
                )
            )

            if run.status == "failed":
                raise ValueError(f"Run failed: {run.last_error}")

            # If the run requires action (function calls), execute tools and continue
            if run.status == "requires_action" and run.required_action is not None:
                tool_calls: List[FunctionCall] = []
                for required_tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    if required_tool_call.type == "function":
                        tool_calls.append(
                            FunctionCall(
                                id=required_tool_call.id,
                                name=required_tool_call.function.name,
                                arguments=required_tool_call.function.arguments,
                            )
                        )

                # Add tool call message to inner messages
                tool_call_msg = ToolCallRequestEvent(source=self.name, content=tool_calls)
                inner_messages.append(tool_call_msg)
                event_logger.debug(tool_call_msg)
                yield tool_call_msg

                # Execute tool calls and get results
                tool_outputs: List[FunctionExecutionResult] = []
                for tool_call in tool_calls:
                    try:
                        result = await self._execute_tool_call(tool_call, cancellation_token)
                        is_error = False
                    except Exception as e:
                        result = f"Error: {e}"
                        is_error = True
                    tool_outputs.append(
                        FunctionExecutionResult(
                            content=result, call_id=tool_call.id, is_error=is_error, name=tool_call.name
                        )
                    )

                # Add tool result message to inner messages
                tool_result_msg = ToolCallExecutionEvent(source=self.name, content=tool_outputs)
                inner_messages.append(tool_result_msg)
                event_logger.debug(tool_result_msg)
                yield tool_result_msg

                # Submit tool outputs back to the run
                run = await cancellation_token.link_future(
                    asyncio.ensure_future(
                        self._client.beta.threads.runs.submit_tool_outputs(  # type: ignore[reportDeprecated]
                            thread_id=self._thread_id,
                            run_id=run.id,
                            tool_outputs=[{"tool_call_id": t.call_id, "output": t.content} for t in tool_outputs],
                        )
                    )
                )
                continue

            if run.status == "completed":
                break

            await asyncio.sleep(0.5)

        # Get messages after run completion
        assistant_messages: AsyncCursorPage[Message] = await cancellation_token.link_future(
            asyncio.ensure_future(
                self._client.beta.threads.messages.list(thread_id=self._thread_id, order="desc", limit=1)  # type: ignore[reportDeprecated]
            )
        )

        if not assistant_messages.data:
            raise ValueError("No messages received from assistant")

        # Get the last message's content
        last_message = assistant_messages.data[0]
        if not last_message.content:
            raise ValueError(f"No content in the last message: {last_message}")

        # Extract text content
        text_content = [content for content in last_message.content if content.type == "text"]
        if not text_content:
            raise ValueError(f"Expected text content in the last message: {last_message.content}")

        # Return the assistant's response as a Response with inner messages
        chat_message = TextMessage(source=self.name, content=text_content[0].text.value)
        yield Response(chat_message=chat_message, inner_messages=inner_messages)