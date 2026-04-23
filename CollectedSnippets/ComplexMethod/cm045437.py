async def reset(self) -> None:
        """Reset the team and its participants to their initial state.

        The team must be stopped before it can be reset.

        Raises:
            RuntimeError: If the team has not been initialized or is currently running.

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

                # Reset the team.
                await team.reset()
                stream = team.run_stream(task="Count from 1 to 10, respond one at a time.")
                async for message in stream:
                    print(message)


            asyncio.run(main())
        """

        if not self._initialized:
            await self._init(self._runtime)

        if self._is_running:
            raise RuntimeError("The group chat is currently running. It must be stopped before it can be reset.")
        self._is_running = True

        if self._embedded_runtime:
            # Start the runtime.
            assert isinstance(self._runtime, SingleThreadedAgentRuntime)
            self._runtime.start()

        try:
            # Send a reset messages to all participants.
            for participant_topic_type in self._participant_topic_types:
                await self._runtime.send_message(
                    GroupChatReset(),
                    recipient=AgentId(type=participant_topic_type, key=self._team_id),
                )
            # Send a reset message to the group chat manager.
            await self._runtime.send_message(
                GroupChatReset(),
                recipient=AgentId(type=self._group_chat_manager_topic_type, key=self._team_id),
            )
        finally:
            if self._embedded_runtime:
                # Stop the runtime.
                assert isinstance(self._runtime, SingleThreadedAgentRuntime)
                await self._runtime.stop_when_idle()

            # Reset the output message queue.
            while not self._output_message_queue.empty():
                self._output_message_queue.get_nowait()

            # Indicate that the team is no longer running.
            self._is_running = False