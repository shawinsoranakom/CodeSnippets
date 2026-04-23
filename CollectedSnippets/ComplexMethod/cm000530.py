async def call_codex(
        self,
        *,
        credentials: APIKeyCredentials,
        model: CodexModel,
        prompt: str,
        system_prompt: str,
        max_output_tokens: int | None,
        reasoning_effort: CodexReasoningEffort,
    ) -> CodexCallResult:
        """Invoke the OpenAI Responses API."""
        client = AsyncOpenAI(api_key=credentials.api_key.get_secret_value())

        request_payload: dict[str, Any] = {
            "model": model.value,
            "input": prompt,
        }
        if system_prompt:
            request_payload["instructions"] = system_prompt
        if max_output_tokens is not None:
            request_payload["max_output_tokens"] = max_output_tokens
        if reasoning_effort != CodexReasoningEffort.NONE:
            request_payload["reasoning"] = {"effort": reasoning_effort.value}

        response = await client.responses.create(**request_payload)
        if not isinstance(response, OpenAIResponse):
            raise TypeError(f"Expected OpenAIResponse, got {type(response).__name__}")

        # Extract data directly from typed response
        text_output = response.output_text or ""
        reasoning_summary = (
            str(response.reasoning.summary)
            if response.reasoning and response.reasoning.summary
            else ""
        )
        response_id = response.id or ""

        # Update usage stats
        self.execution_stats.input_token_count = (
            response.usage.input_tokens if response.usage else 0
        )
        self.execution_stats.output_token_count = (
            response.usage.output_tokens if response.usage else 0
        )
        self.execution_stats.llm_call_count += 1

        return CodexCallResult(
            response=text_output,
            reasoning=reasoning_summary,
            response_id=response_id,
        )