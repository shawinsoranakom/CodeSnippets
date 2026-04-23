async def _astream(  # noqa: C901, PLR0912
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {**params, **kwargs, "stream": True}
        if self.stream_usage:
            params["stream_options"] = {"include_usage": True}
        _strip_internal_kwargs(params)
        sdk_messages = _wrap_messages_for_sdk(message_dicts)

        default_chunk_class: type[BaseMessageChunk] = AIMessageChunk
        async for chunk in await self.client.chat.send_async(
            messages=sdk_messages, **params
        ):
            chunk_dict = chunk.model_dump(by_alias=True)
            if not chunk_dict.get("choices"):
                if error := chunk_dict.get("error"):
                    msg = (
                        f"OpenRouter API returned an error during streaming: "
                        f"{error.get('message', str(error))} "
                        f"(code: {error.get('code', 'unknown')})"
                    )
                    raise ValueError(msg)
                # Usage-only chunk (no choices) — emit with usage_metadata
                if usage := chunk_dict.get("usage"):
                    usage_metadata = _create_usage_metadata(usage)
                    usage_chunk = AIMessageChunk(
                        content="", usage_metadata=usage_metadata
                    )
                    generation_chunk = ChatGenerationChunk(message=usage_chunk)
                    if run_manager:
                        await run_manager.on_llm_new_token(
                            token=generation_chunk.text, chunk=generation_chunk
                        )
                    yield generation_chunk
                continue
            choice = chunk_dict["choices"][0]
            message_chunk = _convert_chunk_to_message_chunk(
                chunk_dict, default_chunk_class
            )
            generation_info: dict[str, Any] = {}
            if finish_reason := choice.get("finish_reason"):
                generation_info["finish_reason"] = finish_reason
                # Include response-level metadata on the final chunk
                response_model = chunk_dict.get("model")
                generation_info["model_name"] = response_model or self.model_name
                if system_fingerprint := chunk_dict.get("system_fingerprint"):
                    generation_info["system_fingerprint"] = system_fingerprint
                if native_finish_reason := choice.get("native_finish_reason"):
                    generation_info["native_finish_reason"] = native_finish_reason
                if response_id := chunk_dict.get("id"):
                    generation_info["id"] = response_id
                if created := chunk_dict.get("created"):
                    generation_info["created"] = int(created)  # UNIX timestamp
                if object_ := chunk_dict.get("object"):
                    generation_info["object"] = object_
            logprobs = choice.get("logprobs")
            if logprobs:
                generation_info["logprobs"] = logprobs

            if generation_info:
                generation_info["model_provider"] = "openrouter"
                message_chunk = message_chunk.model_copy(
                    update={
                        "response_metadata": {
                            **message_chunk.response_metadata,
                            **generation_info,
                        }
                    }
                )

            default_chunk_class = message_chunk.__class__
            generation_chunk = ChatGenerationChunk(
                message=message_chunk, generation_info=generation_info or None
            )

            if run_manager:
                await run_manager.on_llm_new_token(
                    token=generation_chunk.text,
                    chunk=generation_chunk,
                    logprobs=logprobs,
                )
            yield generation_chunk