async def handle_start(self, message: GroupChatStart, ctx: MessageContext) -> None:  # type: ignore
        """Handle the start of a task."""

        # Check if the conversation has already terminated.
        if self._termination_condition is not None and self._termination_condition.terminated:
            early_stop_message = StopMessage(content="The group chat has already terminated.", source=self._name)
            # Signal termination.
            await self._signal_termination(early_stop_message)
            # Stop the group chat.
            return
        assert message is not None and message.messages is not None

        # Validate the group state given all the messages.
        await self.validate_group_state(message.messages)

        # Log the message to the output topic.
        await self.publish_message(message, topic_id=DefaultTopicId(type=self._output_topic_type))
        # Log the message to the output queue.
        for msg in message.messages:
            await self._output_message_queue.put(msg)

        # Outer Loop for first time
        # Create the initial task ledger
        #################################
        # Combine all message contents for task
        self._task = " ".join([msg.to_model_text() for msg in message.messages])
        planning_conversation: List[LLMMessage] = []

        # 1. GATHER FACTS
        # create a closed book task and generate a response and update the chat history
        planning_conversation.append(
            UserMessage(content=self._get_task_ledger_facts_prompt(self._task), source=self._name)
        )
        response = await self._model_client.create(
            self._get_compatible_context(planning_conversation), cancellation_token=ctx.cancellation_token
        )

        assert isinstance(response.content, str)
        self._facts = response.content
        planning_conversation.append(AssistantMessage(content=self._facts, source=self._name))

        # 2. CREATE A PLAN
        ## plan based on available information
        planning_conversation.append(
            UserMessage(content=self._get_task_ledger_plan_prompt(self._team_description), source=self._name)
        )
        response = await self._model_client.create(
            self._get_compatible_context(planning_conversation), cancellation_token=ctx.cancellation_token
        )

        assert isinstance(response.content, str)
        self._plan = response.content

        # Kick things off
        self._n_stalls = 0
        await self._reenter_outer_loop(ctx.cancellation_token)