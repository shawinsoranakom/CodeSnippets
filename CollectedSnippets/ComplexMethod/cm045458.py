async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        # Prepare the task for the team of agents.
        task_messages = list(messages)

        # Run the team of agents.
        result: TaskResult | None = None
        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []
        model_context = self._model_context

        prev_content = await model_context.get_messages()
        if len(prev_content) > 0:
            prev_message = HandoffMessage(
                content="relevant previous messages",
                source=self.name,
                target="",
                context=prev_content,
            )
            task_messages = [prev_message] + task_messages

        if len(task_messages) == 0:
            task = None
        else:
            task = task_messages

        # Use the new output_task_messages parameter to avoid fragile count-based logic
        async for inner_msg in self._team.run_stream(
            task=task, cancellation_token=cancellation_token, output_task_messages=False
        ):
            if isinstance(inner_msg, TaskResult):
                result = inner_msg
            else:
                yield inner_msg
                if isinstance(inner_msg, ModelClientStreamingChunkEvent):
                    # Skip the model client streaming chunk events.
                    continue
                inner_messages.append(inner_msg)
        assert result is not None

        if len(inner_messages) == 0:
            yield Response(
                chat_message=TextMessage(source=self.name, content="No response."),
                inner_messages=[],
                # Response's inner_messages should be empty. Cause that mean is response to outer world.
            )
        else:
            llm_messages: List[LLMMessage] = []

            if self._model_client.model_info.get("multiple_system_messages", False):
                # The model client supports multiple system messages, so we
                llm_messages.append(SystemMessage(content=self._instruction))
            else:
                # The model client does not support multiple system messages, so we
                llm_messages.append(UserMessage(content=self._instruction, source="user"))

            # Generate a response using the model client.
            for message in inner_messages:
                if isinstance(message, BaseChatMessage):
                    llm_messages.append(message.to_model_message())

            if self._model_client.model_info.get("multiple_system_messages", False):
                # The model client supports multiple system messages, so we
                llm_messages.append(SystemMessage(content=self._response_prompt))
            else:
                # The model client does not support multiple system messages, so we
                llm_messages.append(UserMessage(content=self._response_prompt, source="user"))
            completion = await self._model_client.create(messages=llm_messages, cancellation_token=cancellation_token)
            assert isinstance(completion.content, str)
            yield Response(
                chat_message=TextMessage(source=self.name, content=completion.content, models_usage=completion.usage),
                inner_messages=[],
                # Response's inner_messages should be empty. Cause that mean is response to outer world.
            )

        # Add new user/handoff messages to the model context
        await self._add_messages_to_context(
            model_context=model_context,
            messages=messages,
        )

        # Reset the team.
        await self._team.reset()