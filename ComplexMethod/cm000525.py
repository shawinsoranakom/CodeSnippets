async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        has_messages = any(
            isinstance(m, dict)
            and isinstance(m.get("content"), str)
            and bool(m["content"].strip())
            for m in (input_data.messages or [])
        )
        has_prompt = bool(input_data.prompt and input_data.prompt.strip())
        if not has_messages and not has_prompt:
            raise ValueError(
                "Cannot call LLM with no messages and no prompt. "
                "Provide at least one message or a non-empty prompt."
            )

        response = await self.llm_call(
            AIStructuredResponseGeneratorBlock.Input(
                prompt=input_data.prompt,
                credentials=input_data.credentials,
                model=input_data.model,
                conversation_history=input_data.messages,
                max_tokens=input_data.max_tokens,
                expected_format={},
                ollama_host=input_data.ollama_host,
            ),
            credentials=credentials,
        )
        yield "response", response["response"]
        yield "prompt", self.prompt