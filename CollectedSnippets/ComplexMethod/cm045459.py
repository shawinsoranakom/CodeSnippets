async def run(
        self,
        *,
        task: str | BaseChatMessage | Sequence[BaseChatMessage] | None = None,
        cancellation_token: CancellationToken | None = None,
        output_task_messages: bool = True,
    ) -> TaskResult:
        """Run the agent with the given task and return the result."""
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
            elif isinstance(task, BaseChatMessage):
                input_messages.append(task)
                if output_task_messages:
                    output_messages.append(task)
            else:
                if not task:
                    raise ValueError("Task list cannot be empty.")
                # Task is a sequence of messages.
                for msg in task:
                    if isinstance(msg, BaseChatMessage):
                        input_messages.append(msg)
                        if output_task_messages:
                            output_messages.append(msg)
                    else:
                        raise ValueError(f"Invalid message type in sequence: {type(msg)}")
            response = await self.on_messages(input_messages, cancellation_token)
            if response.inner_messages is not None:
                output_messages += response.inner_messages
            output_messages.append(response.chat_message)
            return TaskResult(messages=output_messages)