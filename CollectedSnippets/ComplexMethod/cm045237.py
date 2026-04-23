async def on_messages_stream(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: Optional[CancellationToken] = None,
        message_limit: int = 1,
        polling_interval: float = 0.5,
    ) -> AsyncGenerator[AgentEvent | ChatMessage | Response, None]:
        """
        Process incoming messages and yield streaming responses from the Azure AI agent.

        This method handles the complete interaction flow with the Azure AI agent:
        1. Processing input messages
        2. Creating and monitoring a run
        3. Handling tool calls and their results
        4. Retrieving and returning the agent's final response

        The method yields events during processing (like tool calls) and finally yields
        the complete Response with the agent's message.

        Args:
            messages (Sequence[BaseChatMessage]): The messages to process
            cancellation_token (CancellationToken): Token for cancellation handling
            message_limit (int, optional): Maximum number of messages to retrieve from the thread
            polling_interval (float, optional): Time to sleep between polling for run status

        Yields:
            AgentEvent | ChatMessage | Response: Events during processing and the final response

        Raises:
            ValueError: If the run fails or no message is received from the assistant
        """
        if cancellation_token is None:
            cancellation_token = CancellationToken()

        await self._ensure_initialized()

        # Process all messages in sequence
        for message in messages:
            if isinstance(message, (TextMessage, MultiModalMessage)):
                await self.handle_text_message(str(message.content), cancellation_token)
            elif isinstance(message, (StopMessage, HandoffMessage)):
                await self.handle_text_message(message.content, cancellation_token)

        # Inner messages for tool calls
        inner_messages: List[AgentEvent | ChatMessage] = []

        # Create and start a run
        run: ThreadRun = await cancellation_token.link_future(
            asyncio.ensure_future(
                self._project_client.agents.runs.create(
                    thread_id=self.thread_id,
                    agent_id=self._get_agent_id,
                )
            )
        )

        # Wait for run completion by polling
        while True:
            run = await cancellation_token.link_future(
                asyncio.ensure_future(
                    self._project_client.agents.runs.get(
                        thread_id=self.thread_id,
                        run_id=run.id,
                    )
                )
            )

            if run.status == RunStatus.FAILED:
                raise ValueError(f"Run failed: {run.last_error}")

            # If the run requires action (function calls), execute tools and continue
            if run.status == RunStatus.REQUIRES_ACTION and run.required_action is not None:
                tool_calls: List[FunctionCall] = []
                submit_tool_outputs = getattr(run.required_action, "submit_tool_outputs", None)
                if submit_tool_outputs and hasattr(submit_tool_outputs, "tool_calls"):
                    for required_tool_call in submit_tool_outputs.tool_calls:
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
                trace_logger.debug(tool_call_msg)
                yield tool_call_msg

                # Execute tool calls and get results
                tool_outputs: List[FunctionExecutionResult] = []

                # TODO: Support parallel execution of tool calls

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
                trace_logger.debug(tool_result_msg)
                yield tool_result_msg

                # Submit tool outputs back to the run
                run = await cancellation_token.link_future(
                    asyncio.ensure_future(
                        self._project_client.agents.runs.submit_tool_outputs(
                            thread_id=self.thread_id,
                            run_id=run.id,
                            tool_outputs=[ToolOutput(tool_call_id=t.call_id, output=t.content) for t in tool_outputs],
                        )
                    )
                )
                continue

            if run.status == RunStatus.COMPLETED:
                break

            # TODO support for parameter to control polling interval
            await asyncio.sleep(polling_interval)

        # After run is completed, get the messages
        trace_logger.debug("Retrieving messages from thread")
        # Collect up to message_limit messages in DESCENDING order, support cancellation
        agent_messages: List[ThreadMessage] = []
        async for msg in self._project_client.agents.messages.list(
            thread_id=self.thread_id,
            order=ListSortOrder.DESCENDING,
            limit=message_limit,
        ):
            if cancellation_token.is_cancelled():
                trace_logger.debug("Message retrieval cancelled by token.")
                break
            agent_messages.append(msg)
            if len(agent_messages) >= message_limit:
                break
        if not agent_messages:
            raise ValueError("No messages received from assistant")

        # Get the last message from the agent (role=AGENT)
        last_message: Optional[ThreadMessage] = next(
            (m for m in agent_messages if getattr(m, "role", None) == "agent"), None
        )
        if not last_message:
            trace_logger.debug("No message with AGENT role found, falling back to first message")
            last_message = agent_messages[0]  # Fallback to first message
        if not getattr(last_message, "content", None):
            raise ValueError("No content in the last message")

        # Extract text content
        message_text = ""
        for text_message in last_message.text_messages:
            message_text += text_message.text.value

        # Extract citations
        citations: list[Any] = []

        # Try accessing annotations directly

        annotations = getattr(last_message, "annotations", [])

        if isinstance(annotations, list) and annotations:
            annotations = cast(List[MessageTextUrlCitationAnnotation], annotations)

            trace_logger.debug(f"Found {len(annotations)} annotations")
            for annotation in annotations:
                if hasattr(annotation, "url_citation"):  # type: ignore
                    trace_logger.debug(f"Citation found: {annotation.url_citation.url}")
                    citations.append(
                        {"url": annotation.url_citation.url, "title": annotation.url_citation.title, "text": None}  # type: ignore
                    )
        # For backwards compatibility
        elif hasattr(last_message, "url_citation_annotations") and last_message.url_citation_annotations:
            url_annotations = cast(List[Any], last_message.url_citation_annotations)

            trace_logger.debug(f"Found {len(url_annotations)} URL citations")

            for annotation in url_annotations:
                citations.append(
                    {"url": annotation.url_citation.url, "title": annotation.url_citation.title, "text": None}  # type: ignore
                )

        elif hasattr(last_message, "file_citation_annotations") and last_message.file_citation_annotations:
            file_annotations = cast(List[Any], last_message.file_citation_annotations)

            trace_logger.debug(f"Found {len(file_annotations)} URL citations")

            for annotation in file_annotations:
                citations.append(
                    {"file_id": annotation.file_citation.file_id, "title": None, "text": annotation.file_citation.quote}  # type: ignore
                )

        trace_logger.debug(f"Total citations extracted: {len(citations)}")

        # Create the response message with citations as JSON string
        chat_message = TextMessage(
            source=self.name, content=message_text, metadata={"citations": json.dumps(citations)} if citations else {}
        )

        # Return the assistant's response as a Response with inner messages
        yield Response(chat_message=chat_message, inner_messages=inner_messages)