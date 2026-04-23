async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        *,
        stream_usage: bool | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        kwargs["stream"] = True
        stream_usage = self._should_stream_usage(stream_usage, **kwargs)
        if stream_usage:
            kwargs["stream_options"] = {"include_usage": stream_usage}
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        default_chunk_class: type[BaseMessageChunk] = AIMessageChunk
        base_generation_info = {}

        try:
            if "response_format" in payload:
                if self.include_response_headers:
                    warnings.warn(
                        "Cannot currently include response headers when "
                        "response_format is specified."
                    )
                payload.pop("stream")
                response_stream = self.root_async_client.beta.chat.completions.stream(
                    **payload
                )
                context_manager = response_stream
            else:
                if self.include_response_headers:
                    raw_response = await self.async_client.with_raw_response.create(
                        **payload
                    )
                    response = raw_response.parse()
                    base_generation_info = {"headers": dict(raw_response.headers)}
                else:
                    response = await self.async_client.create(**payload)
                context_manager = response
            async with context_manager as response:
                is_first_chunk = True
                async for chunk in _astream_with_chunk_timeout(
                    response,
                    self.stream_chunk_timeout,
                    model_name=self.model_name,
                ):
                    if not isinstance(chunk, dict):
                        chunk = chunk.model_dump()
                    generation_chunk = self._convert_chunk_to_generation_chunk(
                        chunk,
                        default_chunk_class,
                        base_generation_info if is_first_chunk else {},
                    )
                    if generation_chunk is None:
                        continue
                    default_chunk_class = generation_chunk.message.__class__
                    logprobs = (generation_chunk.generation_info or {}).get("logprobs")
                    if run_manager:
                        await run_manager.on_llm_new_token(
                            generation_chunk.text,
                            chunk=generation_chunk,
                            logprobs=logprobs,
                        )
                    is_first_chunk = False
                    yield generation_chunk
        except openai.BadRequestError as e:
            _handle_openai_bad_request(e)
        except openai.APIError as e:
            _handle_openai_api_error(e)
        if hasattr(response, "get_final_completion") and "response_format" in payload:
            final_completion = await response.get_final_completion()
            generation_chunk = self._get_generation_chunk_from_completion(
                final_completion
            )
            if run_manager:
                await run_manager.on_llm_new_token(
                    generation_chunk.text, chunk=generation_chunk
                )
            yield generation_chunk