def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk,
            default_chunk_class,
            base_generation_info,
        )

        if generation_chunk:
            generation_chunk.message.response_metadata["model_provider"] = "xai"

        if (choices := chunk.get("choices")) and generation_chunk:
            top = choices[0]
            if isinstance(generation_chunk.message, AIMessageChunk) and (
                reasoning_content := top.get("delta", {}).get("reasoning_content")
            ):
                generation_chunk.message.additional_kwargs["reasoning_content"] = (
                    reasoning_content
                )

        if (
            (citations := chunk.get("citations"))
            and generation_chunk
            and isinstance(generation_chunk.message, AIMessageChunk)
            and not chunk.get("usage")  # citations are repeated in final usage chunk
        ):
            generation_chunk.message.additional_kwargs["citations"] = citations

        # Unlike OpenAI, xAI reports reasoning tokens < completion tokens. So we assume
        # they are not counted in output tokens, and we add them here.
        if (
            generation_chunk
            and (not self._use_responses_api({}))
            and (usage_metadata := generation_chunk.message.usage_metadata)  # type: ignore[attr-defined]
            and (
                reasoning_tokens := usage_metadata.get("output_token_details", {}).get(
                    "reasoning"
                )
            )
        ):
            generation_chunk.message.usage_metadata["output_tokens"] += reasoning_tokens  # type: ignore[attr-defined]
        return generation_chunk