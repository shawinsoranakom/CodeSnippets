async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        assert isinstance(message.body, UserMessage)
        self._chat_history.append(message.body)
        # If the message is an approval message from the user, stop the chat.
        if message.body.source == "User":
            assert isinstance(message.body.content, str)
            if message.body.content.lower().strip(string.punctuation).endswith("approve"): # type: ignore
                await self.runtime.publish_message(StreamResult(content="stop", source=self.id.type), topic_id=task_results_topic_id)
                return
        if message.body.source == "Critic":
            #if ("approve" in message.body.content.lower().strip(string.punctuation)):
            if message.body.content.lower().strip(string.punctuation).endswith("approve"): # type: ignore
                stop_msg = AssistantMessage(content="Task Finished", source=self.id.type)
                await self.runtime.publish_message(StreamResult(content=stop_msg, source=self.id.type), topic_id=task_results_topic_id)
                return

        # Simple round robin algorithm to call next client to speak
        selected_topic_type: str
        idx = self._previous_participant_idx +1
        if (idx == len(self._participant_topic_types)):
             idx = 0
        selected_topic_type = self._participant_topic_types[idx]
        self._previous_participant_idx = idx 

        # Send the RequestToSpeak message to next agent
        await self.publish_message(RequestToSpeak(), DefaultTopicId(type=selected_topic_type))