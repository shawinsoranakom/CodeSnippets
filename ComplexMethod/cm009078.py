async def _agenerate(
        self,
        prompts: list[str],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Call out to OpenAI's endpoint async with k unique prompts."""
        params = self._invocation_params
        params = {**params, **kwargs}
        sub_prompts = self.get_sub_prompts(params, prompts, stop)
        choices = []
        token_usage: dict[str, int] = {}
        # Get the token usage from the response.
        # Includes prompt, completion, and total tokens used.
        _keys = {"completion_tokens", "prompt_tokens", "total_tokens"}
        system_fingerprint: str | None = None
        for _prompts in sub_prompts:
            if self.streaming:
                if len(_prompts) > 1:
                    msg = "Cannot stream results with multiple prompts."
                    raise ValueError(msg)

                generation: GenerationChunk | None = None
                async for chunk in self._astream(
                    _prompts[0], stop, run_manager, **kwargs
                ):
                    if generation is None:
                        generation = chunk
                    else:
                        generation += chunk
                if generation is None:
                    msg = "Generation is empty after streaming."
                    raise ValueError(msg)
                choices.append(
                    {
                        "text": generation.text,
                        "finish_reason": (
                            generation.generation_info.get("finish_reason")
                            if generation.generation_info
                            else None
                        ),
                        "logprobs": (
                            generation.generation_info.get("logprobs")
                            if generation.generation_info
                            else None
                        ),
                    }
                )
            else:
                response = await self.async_client.create(prompt=_prompts, **params)
                if not isinstance(response, dict):
                    response = response.model_dump()
                choices.extend(response["choices"])
                _update_token_usage(_keys, response, token_usage)
        return self.create_llm_result(
            choices, prompts, params, token_usage, system_fingerprint=system_fingerprint
        )