async def _astream_responses(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        kwargs["stream"] = True
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        try:
            if self.include_response_headers:
                raw_context_manager = (
                    await self.root_async_client.with_raw_response.responses.create(
                        **payload
                    )
                )
                context_manager = raw_context_manager.parse()
                headers = {"headers": dict(raw_context_manager.headers)}
            else:
                context_manager = await self.root_async_client.responses.create(
                    **payload
                )
                headers = {}
            original_schema_obj = kwargs.get("response_format")

            async with context_manager as response:
                is_first_chunk = True
                current_index = -1
                current_output_index = -1
                current_sub_index = -1
                has_reasoning = False
                async for chunk in _astream_with_chunk_timeout(
                    response,
                    self.stream_chunk_timeout,
                    model_name=self.model_name,
                ):
                    metadata = headers if is_first_chunk else {}
                    (
                        current_index,
                        current_output_index,
                        current_sub_index,
                        generation_chunk,
                    ) = _convert_responses_chunk_to_generation_chunk(
                        chunk,
                        current_index,
                        current_output_index,
                        current_sub_index,
                        schema=original_schema_obj,
                        metadata=metadata,
                        has_reasoning=has_reasoning,
                        output_version=self.output_version,
                    )
                    if generation_chunk:
                        if run_manager:
                            await run_manager.on_llm_new_token(
                                generation_chunk.text, chunk=generation_chunk
                            )
                        is_first_chunk = False
                        if "reasoning" in generation_chunk.message.additional_kwargs:
                            has_reasoning = True
                        yield generation_chunk
        except openai.BadRequestError as e:
            _handle_openai_bad_request(e)
        except openai.APIError as e:
            _handle_openai_api_error(e)