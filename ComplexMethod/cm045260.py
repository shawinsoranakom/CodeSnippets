def _validate_model_info(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema],
        json_output: Optional[bool | type[BaseModel]],
        create_args: Dict[str, Any],
    ) -> None:
        if self.model_info["vision"] is False:
            for message in messages:
                if isinstance(message, UserMessage):
                    if isinstance(message.content, list) and any(isinstance(x, Image) for x in message.content):
                        raise ValueError("Model does not support vision and image was provided")

        if json_output is not None:
            if self.model_info["json_output"] is False and json_output is True:
                raise ValueError("Model does not support JSON output")

            if isinstance(json_output, type):
                # TODO: we should support this in the future.
                raise ValueError("Structured output is not currently supported for AzureAIChatCompletionClient")

            if json_output is True and "response_format" not in create_args:
                create_args["response_format"] = "json_object"

        if self.model_info["json_output"] is False and json_output is True:
            raise ValueError("Model does not support JSON output")
        if self.model_info["function_calling"] is False and len(tools) > 0:
            raise ValueError("Model does not support function calling")