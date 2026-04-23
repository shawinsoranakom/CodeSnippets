async def call_model(
        self,
        summary: str,
        user_content: UserContent,
        system_message_content: str | None = None,
        keep_these_messages: bool = True,
    ) -> str:
        """
        Calls the model client with the given input and returns the response.
        """
        # Prepare the input message list
        if system_message_content is None:
            system_message_content = self.default_system_message_content
        system_message: LLMMessage
        if self.client.model_info["family"] == "o1":
            # No system message allowed, so pass it as the first user message.
            system_message = UserMessage(content=system_message_content, source="User")
        else:
            # System message allowed.
            system_message = SystemMessage(content=system_message_content)

        user_message = UserMessage(content=user_content, source="User")
        input_messages = [system_message] + self._chat_history + [user_message]

        # Double check the types of the input messages.
        for message in input_messages:
            for part in message.content:
                assert isinstance(part, str) or isinstance(part, Image), "Invalid message content type: {}".format(
                    type(part)
                )

        # Call the model
        start_time = time.time()
        response = await self.client.create(input_messages)
        assert isinstance(response, CreateResult)
        response_string = response.content
        assert isinstance(response_string, str)
        response_message = AssistantMessage(content=response_string, source="Assistant")
        assert isinstance(response_message, AssistantMessage)
        self.time_spent_in_model_calls += time.time() - start_time
        self.num_model_calls += 1

        # Log the model call
        self.logger.log_model_call(summary=summary, input_messages=input_messages, response=response)

        # Manage the chat history
        if keep_these_messages:
            self._chat_history.append(user_message)
            self._chat_history.append(response_message)

        # Return the response as a string for now
        return response_string