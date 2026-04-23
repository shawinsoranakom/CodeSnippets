async def run_stream(
        self,
        *,
        task: str | BaseChatMessage | Sequence[BaseChatMessage] | None = None,
        cancellation_token: CancellationToken | None = None,
        output_task_messages: bool = True,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None]:
        """Run the team and produces a stream of messages and the final result
        of the type :class:`~autogen_agentchat.base.TaskResult` as the last item in the stream. Once the
        team is stopped, the termination condition is reset.

        .. note::

            If an agent produces :class:`~autogen_agentchat.messages.ModelClientStreamingChunkEvent`,
            the message will be yielded in the stream but it will not be included in the
            :attr:`~autogen_agentchat.base.TaskResult.messages`.

        Args:
            task (str | BaseChatMessage | Sequence[BaseChatMessage] | None): The task to run the team with. Can be a string, a single :class:`BaseChatMessage` , or a list of :class:`BaseChatMessage`.
            cancellation_token (CancellationToken | None): The cancellation token to kill the task immediately.
                Setting the cancellation token potentially put the team in an inconsistent state,
                and it may not reset the termination condition.
                To gracefully stop the team, use :class:`~autogen_agentchat.conditions.ExternalTermination` instead.
            output_task_messages (bool): Whether to include task messages in the output stream. Defaults to True for backward compatibility.

        Returns:
            stream: an :class:`~collections.abc.AsyncGenerator` that yields :class:`~autogen_agentchat.messages.BaseAgentEvent`, :class:`~autogen_agentchat.messages.BaseChatMessage`, and the final result :class:`~autogen_agentchat.base.TaskResult` as the last item in the stream.

        Example using the :class:`~autogen_agentchat.teams.RoundRobinGroupChat` team:

        .. code-block:: python

            import asyncio
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.conditions import MaxMessageTermination
            from autogen_agentchat.teams import RoundRobinGroupChat
            from autogen_ext.models.openai import OpenAIChatCompletionClient


            async def main() -> None:
                model_client = OpenAIChatCompletionClient(model="gpt-4o")

                agent1 = AssistantAgent("Assistant1", model_client=model_client)
                agent2 = AssistantAgent("Assistant2", model_client=model_client)
                termination = MaxMessageTermination(3)
                team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)

                stream = team.run_stream(task="Count from 1 to 10, respond one at a time.")
                async for message in stream:
                    print(message)

                # Run the team again without a task to continue the previous task.
                stream = team.run_stream()
                async for message in stream:
                    print(message)


            asyncio.run(main())


        Example using the :class:`~autogen_core.CancellationToken` to cancel the task:

        .. code-block:: python

            import asyncio
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.conditions import MaxMessageTermination
            from autogen_agentchat.ui import Console
            from autogen_agentchat.teams import RoundRobinGroupChat
            from autogen_core import CancellationToken
            from autogen_ext.models.openai import OpenAIChatCompletionClient


            async def main() -> None:
                model_client = OpenAIChatCompletionClient(model="gpt-4o")

                agent1 = AssistantAgent("Assistant1", model_client=model_client)
                agent2 = AssistantAgent("Assistant2", model_client=model_client)
                termination = MaxMessageTermination(3)
                team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)

                cancellation_token = CancellationToken()

                # Create a task to run the team in the background.
                run_task = asyncio.create_task(
                    Console(
                        team.run_stream(
                            task="Count from 1 to 10, respond one at a time.",
                            cancellation_token=cancellation_token,
                        )
                    )
                )

                # Wait for 1 second and then cancel the task.
                await asyncio.sleep(1)
                cancellation_token.cancel()

                # This will raise a cancellation error.
                await run_task


            asyncio.run(main())

        """
        # Create the messages list if the task is a string or a chat message.
        messages: List[BaseChatMessage] | None = None
        if task is None:
            pass
        elif isinstance(task, str):
            messages = [TextMessage(content=task, source="user")]
        elif isinstance(task, BaseChatMessage):
            messages = [task]
        elif isinstance(task, list):
            if not task:
                raise ValueError("Task list cannot be empty.")
            messages = []
            for msg in task:
                if not isinstance(msg, BaseChatMessage):
                    raise ValueError("All messages in task list must be valid BaseChatMessage types")
                messages.append(msg)
        else:
            raise ValueError("Task must be a string, a BaseChatMessage, or a list of BaseChatMessage.")
        # Check if the messages types are registered with the message factory.
        if messages is not None:
            for msg in messages:
                if not self._message_factory.is_registered(msg.__class__):
                    raise ValueError(
                        f"Message type {msg.__class__} is not registered with the message factory. "
                        "Please register it with the message factory by adding it to the "
                        "custom_message_types list when creating the team."
                    )

        if self._is_running:
            raise ValueError("The team is already running, it cannot run again until it is stopped.")
        self._is_running = True

        if self._embedded_runtime:
            # Start the embedded runtime.
            assert isinstance(self._runtime, SingleThreadedAgentRuntime)
            self._runtime.start()

        if not self._initialized:
            await self._init(self._runtime)

        shutdown_task: asyncio.Task[None] | None = None
        if self._embedded_runtime:

            async def stop_runtime() -> None:
                assert isinstance(self._runtime, SingleThreadedAgentRuntime)
                try:
                    # This will propagate any exceptions raised.
                    await self._runtime.stop_when_idle()
                    # Put a termination message in the queue to indicate that the group chat is stopped for whatever reason
                    # but not due to an exception.
                    await self._output_message_queue.put(
                        GroupChatTermination(
                            message=StopMessage(
                                content="The group chat is stopped.", source=self._group_chat_manager_name
                            )
                        )
                    )
                except Exception as e:
                    # Stop the consumption of messages and end the stream.
                    # NOTE: we also need to put a GroupChatTermination event here because when the runtime
                    # has an exception, the group chat manager may not be able to put a GroupChatTermination event in the queue.
                    # This may not be necessary if the group chat manager is able to handle the exception and put the event in the queue.
                    await self._output_message_queue.put(
                        GroupChatTermination(
                            message=StopMessage(
                                content="An exception occurred in the runtime.", source=self._group_chat_manager_name
                            ),
                            error=SerializableException.from_exception(e),
                        )
                    )

            # Create a background task to stop the runtime when the group chat
            # is stopped or has an exception.
            shutdown_task = asyncio.create_task(stop_runtime())

        try:
            # Run the team by sending the start message to the group chat manager.
            # The group chat manager will start the group chat by relaying the message to the participants
            # and the group chat manager.
            await self._runtime.send_message(
                GroupChatStart(messages=messages, output_task_messages=output_task_messages),
                recipient=AgentId(type=self._group_chat_manager_topic_type, key=self._team_id),
                cancellation_token=cancellation_token,
            )
            # Collect the output messages in order.
            output_messages: List[BaseAgentEvent | BaseChatMessage] = []
            stop_reason: str | None = None

            # Yield the messages until the queue is empty.
            while True:
                message_future = asyncio.ensure_future(self._output_message_queue.get())
                if cancellation_token is not None:
                    cancellation_token.link_future(message_future)
                # Wait for the next message, this will raise an exception if the task is cancelled.
                message = await message_future
                if isinstance(message, GroupChatTermination):
                    # If the message contains an error, we need to raise it here.
                    # This will stop the team and propagate the error.
                    if message.error is not None:
                        raise RuntimeError(str(message.error))
                    stop_reason = message.message.content
                    break
                yield message
                if isinstance(message, ModelClientStreamingChunkEvent):
                    # Skip the model client streaming chunk events.
                    continue
                output_messages.append(message)

            # Yield the final result.
            yield TaskResult(messages=output_messages, stop_reason=stop_reason)

        finally:
            try:
                if shutdown_task is not None:
                    # Wait for the shutdown task to finish.
                    # This will propagate any exceptions raised.
                    await shutdown_task
            finally:
                # Clear the output message queue.
                while not self._output_message_queue.empty():
                    self._output_message_queue.get_nowait()

                # Indicate that the team is no longer running.
                self._is_running = False