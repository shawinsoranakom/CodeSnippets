async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.streaming:
            stream_iter = self._astream(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            if stream_iter:
                return await agenerate_from_stream(stream_iter)
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {**params, **kwargs}
        response = await self.async_client.chat.completions.create(
            messages=message_dicts, **params
        )

        if hasattr(response, "usage") and response.usage:
            usage_dict = response.usage.model_dump()
            usage_metadata = _create_usage_metadata(usage_dict)
        else:
            usage_metadata = None
            usage_dict = {}

        additional_kwargs = {}
        for attr in ["citations", "images", "related_questions", "search_results"]:
            if hasattr(response, attr) and getattr(response, attr):
                additional_kwargs[attr] = getattr(response, attr)

        if hasattr(response, "videos") and response.videos:
            additional_kwargs["videos"] = [
                v.model_dump() if hasattr(v, "model_dump") else v
                for v in response.videos
            ]

        if hasattr(response, "reasoning_steps") and response.reasoning_steps:
            additional_kwargs["reasoning_steps"] = [
                r.model_dump() if hasattr(r, "model_dump") else r
                for r in response.reasoning_steps
            ]

        response_metadata: dict[str, Any] = {
            "model_name": getattr(response, "model", self.model)
        }
        if num_search_queries := usage_dict.get("num_search_queries"):
            response_metadata["num_search_queries"] = num_search_queries
        if search_context_size := usage_dict.get("search_context_size"):
            response_metadata["search_context_size"] = search_context_size

        message = AIMessage(
            content=response.choices[0].message.content,
            additional_kwargs=additional_kwargs,
            usage_metadata=usage_metadata,
            response_metadata=response_metadata,
        )
        return ChatResult(generations=[ChatGeneration(message=message)])