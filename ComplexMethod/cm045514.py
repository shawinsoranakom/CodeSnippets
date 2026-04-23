async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        assert isinstance(message.body, UserMessage)

        self._chat_history.append(message.body)  # type: ignore[reportargumenttype,arg-type]

        # Format message history.
        messages: List[str] = []
        for msg in self._chat_history:
            if isinstance(msg.content, str):  # type: ignore[attr-defined]
                messages.append(f"{msg.source}: {msg.content}")  # type: ignore[attr-defined]
            elif isinstance(msg.content, list):  # type: ignore[attr-defined]
                messages.append(f"{msg.source}: {', '.join(msg.content)}")  # type: ignore[attr-defined,reportUnknownArgumentType]
        history = "\n".join(messages)
        # Format roles.
        roles = "\n".join(
            [
                f"{topic_type}: {description}".strip()
                for topic_type, description in zip(
                    self._participant_topic_types, self._participant_descriptions, strict=True
                )
                if topic_type != self._previous_participant_topic_type
            ]
        )
        participants = str(
            [
                topic_type
                for topic_type in self._participant_topic_types
                if topic_type != self._previous_participant_topic_type
            ]
        )

        selector_prompt = f"""You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to play. Only return the role.

{history}

Read the above conversation. Then select the next role from {participants} to play. if you think it's enough talking (for example they have talked for {self._max_rounds} rounds), return 'FINISH'.
"""
        system_message = SystemMessage(content=selector_prompt)
        completion = await self._model_client.create([system_message], cancellation_token=ctx.cancellation_token)

        assert isinstance(
            completion.content, str
        ), f"Completion content must be a string, but is: {type(completion.content)}"

        if completion.content.upper() == "FINISH":
            finish_msg = "I think it's enough iterations on the story! Thanks for collaborating!"
            manager_message = f"\n{'-'*80}\n Manager ({id(self)}): {finish_msg}"
            await publish_message_to_ui(
                runtime=self, source=self.id.type, user_message=finish_msg, ui_config=self._ui_config
            )
            self.console.print(Markdown(manager_message))
            return

        selected_topic_type: str
        for topic_type in self._participant_topic_types:
            if topic_type.lower() in completion.content.lower():
                selected_topic_type = topic_type
                self._previous_participant_topic_type = selected_topic_type
                self.console.print(
                    Markdown(f"\n{'-'*80}\n Manager ({id(self)}): Asking `{selected_topic_type}` to speak")
                )
                await self.publish_message(RequestToSpeak(), DefaultTopicId(type=selected_topic_type))
                return
        raise ValueError(f"Invalid role selected: {completion.content}")