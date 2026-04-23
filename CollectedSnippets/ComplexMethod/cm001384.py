def count_message_tokens(
        self,
        messages: ChatMessage | list[ChatMessage],
        model_name: OpenAIModelName,
    ) -> int:
        if isinstance(messages, ChatMessage):
            messages = [messages]

        if model_name.startswith("gpt-3.5-turbo"):
            tokens_per_message = (
                4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            )
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif (
            model_name.startswith("gpt-4")
            or model_name.startswith("gpt-5")
            or model_name.startswith("o1")
            or model_name.startswith("o3")
            or model_name.startswith("o4")
        ):
            # GPT-4, GPT-4o, GPT-4.1, GPT-5, and O-series models all use similar format
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            raise NotImplementedError(
                f"count_message_tokens() is not implemented for model {model_name}.\n"
                "See https://github.com/openai/openai-python/blob/120d225b91a8453e15240a49fb1c6794d8119326/chatml.md "  # noqa
                "for information on how messages are converted to tokens."
            )
        tokenizer = self.get_tokenizer(model_name)

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.model_dump().items():
                num_tokens += len(tokenizer.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens