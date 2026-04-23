async def run_stream(
        self,
        *,
        task: str | BaseChatMessage | Sequence[BaseChatMessage] | None = None,
        cancellation_token: CancellationToken | None = None,
        output_task_messages: bool = True,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None]:
        """Run the agent with the given task and return a stream of messages
        and the final task result as the last item in the stream.

        Args:
            task: The task to run. Can be a string, a single message, or a sequence of messages.
            cancellation_token: The cancellation token to kill the task immediately.
            output_task_messages: Whether to include task messages in the output stream. Defaults to True for backward compatibility.
        """
        with trace_invoke_agent_span(
            agent_name=self.name,
            agent_description=self.description,
        ):
            if cancellation_token is None:
                cancellation_token = CancellationToken()
            input_messages: List[BaseChatMessage] = []
            output_messages: List[BaseAgentEvent | BaseChatMessage] = []
            if task is None:
                pass
            elif isinstance(task, str):
                text_msg = TextMessage(content=task, source="user")
                input_messages.append(text_msg)
                if output_task_messages:
                    output_messages.append(text_msg)
                    yield text_msg
            elif isinstance(task, BaseChatMessage):
                input_messages.append(task)
                if output_task_messages:
                    output_messages.append(task)
                    yield task
            else:
                if not task:
                    raise ValueError("Task list cannot be empty.")
                for msg in task:
                    if isinstance(msg, BaseChatMessage):
                        input_messages.append(msg)
                        if output_task_messages:
                            output_messages.append(msg)
                            yield msg
                    else:
                        raise ValueError(f"Invalid message type in sequence: {type(msg)}")
            async for message in self.on_messages_stream(input_messages, cancellation_token):
                if isinstance(message, Response):
                    yield message.chat_message
                    output_messages.append(message.chat_message)
                    yield TaskResult(messages=output_messages)
                else:
                    yield message
                    if isinstance(message, ModelClientStreamingChunkEvent):
                        # Skip the model client streaming chunk events.
                        continue
                    output_messages.append(message)