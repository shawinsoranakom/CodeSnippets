def _generate_with_cache(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        llm_cache = self.cache if isinstance(self.cache, BaseCache) else get_llm_cache()
        # We should check the cache unless it's explicitly set to False
        # A None cache means we should use the default global cache
        # if it's configured.
        check_cache = self.cache or self.cache is None
        if check_cache:
            if llm_cache:
                llm_string = self._get_llm_string(stop=stop, **kwargs)
                normalized_messages = [
                    (
                        msg.model_copy(update={"id": None})
                        if getattr(msg, "id", None) is not None
                        else msg
                    )
                    for msg in messages
                ]
                prompt = dumps(normalized_messages)
                cache_val = llm_cache.lookup(prompt, llm_string)
                if isinstance(cache_val, list):
                    converted_generations = self._convert_cached_generations(cache_val)
                    return ChatResult(generations=converted_generations)
            elif self.cache is None:
                pass
            else:
                msg = "Asked to cache, but no cache found at `langchain.cache`."
                raise ValueError(msg)

        # Apply the rate limiter after checking the cache, since
        # we usually don't want to rate limit cache lookups, but
        # we do want to rate limit API requests.
        if self.rate_limiter:
            self.rate_limiter.acquire(blocking=True)

        # If stream is not explicitly set, check if implicitly requested by
        # astream_events() or astream_log(). Bail out if _stream not implemented
        if self._should_stream(
            async_api=False,
            run_manager=run_manager,
            **kwargs,
        ):
            chunks: list[ChatGenerationChunk] = []
            run_id: str | None = (
                f"{LC_ID_PREFIX}-{run_manager.run_id}" if run_manager else None
            )
            yielded = False
            index = -1
            index_type = ""
            for chunk in self._stream(messages, stop=stop, **kwargs):
                chunk.message.response_metadata = _gen_info_and_msg_metadata(chunk)
                if self.output_version == "v1":
                    # Overwrite .content with .content_blocks
                    chunk.message = _update_message_content_to_blocks(
                        chunk.message, "v1"
                    )
                    for block in cast(
                        "list[types.ContentBlock]", chunk.message.content
                    ):
                        if block["type"] != index_type:
                            index_type = block["type"]
                            index += 1
                        if "index" not in block:
                            block["index"] = index
                if run_manager:
                    if chunk.message.id is None:
                        chunk.message.id = run_id
                    run_manager.on_llm_new_token(
                        cast("str", chunk.message.content), chunk=chunk
                    )
                chunks.append(chunk)
                yielded = True

            # Yield a final empty chunk with chunk_position="last" if not yet yielded
            if (
                yielded
                and isinstance(chunk.message, AIMessageChunk)
                and not chunk.message.chunk_position
            ):
                empty_content: str | list = (
                    "" if isinstance(chunk.message.content, str) else []
                )
                chunk = ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=empty_content, chunk_position="last", id=run_id
                    )
                )
                if run_manager:
                    run_manager.on_llm_new_token("", chunk=chunk)
                chunks.append(chunk)
            result = generate_from_stream(iter(chunks))
        elif inspect.signature(self._generate).parameters.get("run_manager"):
            result = self._generate(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
        else:
            result = self._generate(messages, stop=stop, **kwargs)

        if self.output_version == "v1":
            # Overwrite .content with .content_blocks
            for generation in result.generations:
                generation.message = _update_message_content_to_blocks(
                    generation.message, "v1"
                )

        # Add response metadata to each generation
        for idx, generation in enumerate(result.generations):
            if run_manager and generation.message.id is None:
                generation.message.id = f"{LC_ID_PREFIX}-{run_manager.run_id}-{idx}"
            generation.message.response_metadata = _gen_info_and_msg_metadata(
                generation
            )
        if len(result.generations) == 1 and result.llm_output is not None:
            result.generations[0].message.response_metadata = {
                **result.llm_output,
                **result.generations[0].message.response_metadata,
            }
        if check_cache and llm_cache:
            llm_cache.update(prompt, llm_string, result.generations)
        return result