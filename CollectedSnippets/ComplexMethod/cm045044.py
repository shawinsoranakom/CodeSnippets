async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")

        # Build the context
        for message in messages:
            if isinstance(message, TextMessage):
                self._context.append(UserMessage(content=message.content, source=message.source))
            elif isinstance(message, MultiModalMessage):
                if self._model_client.model_info["vision"]:
                    self._context.append(UserMessage(content=message.content, source=message.source))
                else:
                    self._context.append(UserMessage(content=content_to_str(message.content), source=message.source))

        if len(self._context) == 0:
            return None

        # Call the model to evaluate
        response = await self._model_client.create(self._context + [UserMessage(content=self._prompt, source="user")]) 

        # Check for termination
        if isinstance(message.content, str) and self._termination_phrase in response.content:
            self._terminated = True
            return StopMessage(content=message.content, source="LLMTermination")
        return None