async def serve_tokens_stream_generator(
        self,
        request: GenerateRequest,
        result_generator: AsyncGenerator[RequestOutput, None],
        request_id: str,
        model_name: str,
        request_metadata: RequestResponseMetadata,
    ) -> AsyncGenerator[str, None]:
        num_prompt_tokens = 0
        num_generated_tokens: list[int] = []
        first_iteration = True
        num_cached_tokens = None
        sampling_params: SamplingParams = request.sampling_params

        include_usage, include_continuous_usage = should_include_usage(
            request.stream_options, False
        )

        try:
            async for res in result_generator:
                if first_iteration:
                    if res.prompt_token_ids is not None:
                        num_prompt_tokens = len(res.prompt_token_ids)
                    if res.encoder_prompt_token_ids is not None:
                        num_prompt_tokens += len(res.encoder_prompt_token_ids)
                    num_cached_tokens = res.num_cached_tokens
                    num_generated_tokens = [0] * len(res.outputs)
                    first_iteration = False

                for output in res.outputs:
                    i = output.index
                    delta_token_ids = output.token_ids
                    num_generated_tokens[i] += len(delta_token_ids)

                    finish_reason = output.finish_reason
                    self._raise_if_error(finish_reason, request_id)

                    if not delta_token_ids:
                        continue

                    if sampling_params.logprobs is not None:
                        out_logprobs = output.logprobs
                        assert out_logprobs is not None, "Did not output logprobs"
                        logprobs = self._create_tokens_logprobs(
                            token_ids=delta_token_ids,
                            top_logprobs=out_logprobs,
                            num_output_top_logprobs=sampling_params.logprobs,
                        )
                    else:
                        logprobs = None

                    chunk = GenerateStreamResponse(
                        request_id=request_id,
                        choices=[
                            GenerateResponseStreamChoice(
                                index=i,
                                logprobs=logprobs,
                                finish_reason=finish_reason,
                                token_ids=as_list(delta_token_ids),
                            )
                        ],
                    )
                    if include_continuous_usage:
                        chunk.usage = UsageInfo(
                            prompt_tokens=num_prompt_tokens,
                            completion_tokens=num_generated_tokens[i],
                            total_tokens=(num_prompt_tokens + num_generated_tokens[i]),
                        )

                    yield f"data: {chunk.model_dump_json()}\n\n"

            total_completion_tokens = sum(num_generated_tokens)
            final_usage_info = UsageInfo(
                prompt_tokens=num_prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=num_prompt_tokens + total_completion_tokens,
            )

            if self.enable_prompt_tokens_details and num_cached_tokens:
                final_usage_info.prompt_tokens_details = PromptTokenUsageInfo(
                    cached_tokens=num_cached_tokens
                )

            if include_usage:
                final_chunk = GenerateStreamResponse(
                    request_id=request_id,
                    choices=[],
                    usage=final_usage_info,
                )
                yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"

            request_metadata.final_usage_info = final_usage_info

        except GenerationError as e:
            yield (
                f"data: {self._convert_generation_error_to_streaming_response(e)}\n\n"
            )
        except Exception as e:
            logger.exception("Error in token generation stream.")
            data = self.create_streaming_error_response(e)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"