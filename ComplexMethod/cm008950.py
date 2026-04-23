def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Top Level call."""
        is_native = kwargs.get("response_format")

        if self.tool_calls:
            if is_native:
                tool_calls = (
                    self.tool_calls[self.index] if self.index < len(self.tool_calls) else []
                )
            else:
                tool_calls = self.tool_calls[self.index % len(self.tool_calls)]
        else:
            tool_calls = []

        if is_native and not tool_calls:
            if isinstance(self.structured_response, BaseModel):
                content_obj = self.structured_response.model_dump()
            elif is_dataclass(self.structured_response) and not isinstance(
                self.structured_response, type
            ):
                content_obj = asdict(self.structured_response)
            elif isinstance(self.structured_response, dict):
                content_obj = self.structured_response
            message = AIMessage(content=json.dumps(content_obj), id=str(self.index))
        else:
            messages_string = "-".join([m.text for m in messages])
            message = AIMessage(
                content=messages_string,
                id=str(self.index),
                tool_calls=tool_calls.copy(),
            )
        self.index += 1
        return ChatResult(generations=[ChatGeneration(message=message)])