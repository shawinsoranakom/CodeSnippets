def _get_chat_completion_args(
        self,
        prompt_messages: list[ChatMessage],
        model: LlamafileModelName,
        functions: list[CompletionModelFunction] | None = None,
        max_output_tokens: int | None = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        **kwargs,
    ) -> tuple[
        list[ChatCompletionMessageParam], CompletionCreateParams, dict[str, Any]
    ]:
        messages, completion_kwargs, parse_kwargs = super()._get_chat_completion_args(
            prompt_messages,
            model,
            functions,
            max_output_tokens,
            reasoning_effort,
            **kwargs,
        )

        if model == LlamafileModelName.MISTRAL_7B_INSTRUCT:
            messages = self._adapt_chat_messages_for_mistral_instruct(messages)

        if "seed" not in kwargs and self._configuration.seed is not None:
            completion_kwargs["seed"] = self._configuration.seed

        # Convert all messages with content blocks to simple text messages
        for message in messages:
            if isinstance(content := message.get("content"), list):
                message["content"] = "\n\n".join(
                    b["text"]
                    for b in content
                    if b["type"] == "text"
                    # FIXME: add support for images through image_data completion kwarg
                )

        return messages, completion_kwargs, parse_kwargs