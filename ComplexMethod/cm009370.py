def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)

        params = {**params, **kwargs, "stream": True}

        default_chunk_class: type[BaseMessageChunk] = AIMessageChunk
        for chunk in self.client.create(messages=message_dicts, **params):
            if not isinstance(chunk, dict):
                chunk = chunk.model_dump()  # noqa: PLW2901
            if len(chunk["choices"]) == 0:
                continue
            choice = chunk["choices"][0]
            message_chunk = _convert_chunk_to_message_chunk(chunk, default_chunk_class)
            generation_info = {}
            if finish_reason := choice.get("finish_reason"):
                generation_info["finish_reason"] = finish_reason
                generation_info["model_name"] = self.model_name
                if system_fingerprint := chunk.get("system_fingerprint"):
                    generation_info["system_fingerprint"] = system_fingerprint
                service_tier = params.get("service_tier") or self.service_tier
                generation_info["service_tier"] = service_tier
                reasoning_effort = (
                    params.get("reasoning_effort") or self.reasoning_effort
                )
                if reasoning_effort:
                    generation_info["reasoning_effort"] = reasoning_effort
            logprobs = choice.get("logprobs")
            if logprobs:
                generation_info["logprobs"] = logprobs

            if generation_info:
                message_chunk = message_chunk.model_copy(
                    update={"response_metadata": generation_info}
                )

            default_chunk_class = message_chunk.__class__
            generation_chunk = ChatGenerationChunk(
                message=message_chunk, generation_info=generation_info or None
            )

            if run_manager:
                run_manager.on_llm_new_token(
                    generation_chunk.text, chunk=generation_chunk, logprobs=logprobs
                )
            yield generation_chunk