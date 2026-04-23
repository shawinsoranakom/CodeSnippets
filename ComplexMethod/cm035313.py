def format_messages_for_llm(self, messages: Message | list[Message]) -> list[dict]:
        if isinstance(messages, Message):
            messages = [messages]

        # set flags to know how to serialize the messages
        for message in messages:
            message.cache_enabled = self.is_caching_prompt_active()
            message.vision_enabled = self.vision_is_active()
            message.function_calling_enabled = self.is_function_calling_active()
            if 'deepseek' in self.config.model:
                message.force_string_serializer = True
            if 'kimi-k2-instruct' in self.config.model and 'groq' in self.config.model:
                message.force_string_serializer = True
            if any(
                k in self.config.model
                for k in (
                    'openrouter/anthropic/claude-sonnet-4',
                    'openrouter/anthropic/claude-opus-4-6',
                    'openrouter/anthropic/claude-sonnet-4-5-20250929',
                    'openrouter/anthropic/claude-haiku-4-5-20251001',
                )
            ):
                message.force_string_serializer = True

        # let pydantic handle the serialization
        return [message.model_dump() for message in messages]