def _create_chat_result(
        self,
        response: dict | openai.BaseModel,
        generation_info: dict | None = None,
    ) -> ChatResult:
        rtn = super()._create_chat_result(response, generation_info)

        for generation in rtn.generations:
            generation.message.response_metadata["model_provider"] = "xai"

        if not isinstance(response, openai.BaseModel):
            return rtn

        if hasattr(response.choices[0].message, "reasoning_content"):  # type: ignore[attr-defined]
            rtn.generations[0].message.additional_kwargs["reasoning_content"] = (
                response.choices[0].message.reasoning_content  # type: ignore[attr-defined]
            )

        if hasattr(response, "citations"):
            rtn.generations[0].message.additional_kwargs["citations"] = (
                response.citations
            )

        # Unlike OpenAI, xAI reports reasoning tokens < completion tokens. So we assume
        # they are not counted in output tokens, and we add them here.
        if (
            (not self._use_responses_api({}))
            and (usage_metadata := rtn.generations[0].message.usage_metadata)  # type: ignore[attr-defined]
            and (
                reasoning_tokens := usage_metadata.get("output_token_details", {}).get(
                    "reasoning"
                )
            )
        ):
            rtn.generations[0].message.usage_metadata["output_tokens"] += (  # type: ignore[attr-defined]
                reasoning_tokens
            )

        return rtn