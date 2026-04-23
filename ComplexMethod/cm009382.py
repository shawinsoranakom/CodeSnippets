async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {**params, **kwargs}
        default_chunk_class = AIMessageChunk
        params.pop("stream", None)
        if stop:
            params["stop_sequences"] = stop
        stream_resp = await self.async_client.chat.completions.create(
            messages=message_dicts, stream=True, **params
        )
        first_chunk = True
        prev_total_usage: UsageMetadata | None = None

        added_model_name: bool = False
        added_search_queries: bool = False
        async for chunk in stream_resp:
            if not isinstance(chunk, dict):
                chunk = chunk.model_dump()
            if total_usage := chunk.get("usage"):
                lc_total_usage = _create_usage_metadata(total_usage)
                if prev_total_usage:
                    usage_metadata: UsageMetadata | None = subtract_usage(
                        lc_total_usage, prev_total_usage
                    )
                else:
                    usage_metadata = lc_total_usage
                prev_total_usage = lc_total_usage
            else:
                usage_metadata = None
            if len(chunk["choices"]) == 0:
                continue
            choice = chunk["choices"][0]

            additional_kwargs = {}
            if first_chunk:
                additional_kwargs["citations"] = chunk.get("citations", [])
                for attr in ["images", "related_questions", "search_results"]:
                    if attr in chunk:
                        additional_kwargs[attr] = chunk[attr]

                if chunk.get("videos"):
                    additional_kwargs["videos"] = chunk["videos"]

                if chunk.get("reasoning_steps"):
                    additional_kwargs["reasoning_steps"] = chunk["reasoning_steps"]

            generation_info = {}
            if (model_name := chunk.get("model")) and not added_model_name:
                generation_info["model_name"] = model_name
                added_model_name = True

            if total_usage := chunk.get("usage"):
                if num_search_queries := total_usage.get("num_search_queries"):
                    if not added_search_queries:
                        generation_info["num_search_queries"] = num_search_queries
                        added_search_queries = True
                if search_context_size := total_usage.get("search_context_size"):
                    generation_info["search_context_size"] = search_context_size

            chunk = self._convert_delta_to_message_chunk(
                choice["delta"], default_chunk_class
            )

            if isinstance(chunk, AIMessageChunk) and usage_metadata:
                chunk.usage_metadata = usage_metadata

            if first_chunk:
                chunk.additional_kwargs |= additional_kwargs
                first_chunk = False

            if finish_reason := choice.get("finish_reason"):
                generation_info["finish_reason"] = finish_reason

            default_chunk_class = chunk.__class__
            chunk = ChatGenerationChunk(message=chunk, generation_info=generation_info)
            if run_manager:
                await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield chunk