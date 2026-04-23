async def completion_stream_generator(
        self,
        request: CompletionRequest,
        engine_inputs: list[EngineInput],
        result_generator: AsyncIterator[tuple[int, RequestOutput]],
        request_id: str,
        created_time: int,
        model_name: str,
        num_prompts: int,
        tokenizer: TokenizerLike | None,
        request_metadata: RequestResponseMetadata,
    ) -> AsyncGenerator[str, None]:
        num_choices = 1 if request.n is None else request.n
        previous_text_lens = [0] * num_choices * num_prompts
        previous_num_tokens = [0] * num_choices * num_prompts
        has_echoed = [False] * num_choices * num_prompts
        num_prompt_tokens = [0] * num_prompts
        num_cached_tokens = None
        first_iteration = True

        stream_options = request.stream_options
        include_usage, include_continuous_usage = should_include_usage(
            stream_options, self.enable_force_include_usage
        )

        try:
            async for prompt_idx, res in result_generator:
                prompt_token_ids = res.prompt_token_ids
                prompt_logprobs = res.prompt_logprobs

                if first_iteration:
                    num_cached_tokens = res.num_cached_tokens
                    first_iteration = False

                prompt_text = res.prompt
                if prompt_text is None:
                    engine_input = engine_inputs[prompt_idx]
                    prompt_text = self._extract_prompt_text(engine_input)

                # Prompt details are excluded from later streamed outputs
                if prompt_token_ids is not None:
                    num_prompt_tokens[prompt_idx] = len(prompt_token_ids)

                delta_token_ids: GenericSequence[int]
                out_logprobs: GenericSequence[dict[int, Logprob] | None] | None

                for output in res.outputs:
                    i = output.index + prompt_idx * num_choices

                    # Useful when request.return_token_ids is True
                    # Returning prompt token IDs shares the same logic
                    # with the echo implementation.
                    prompt_token_ids_to_return: list[int] | None = None

                    assert request.max_tokens is not None
                    if request.echo and not has_echoed[i]:
                        assert prompt_token_ids is not None
                        if request.return_token_ids:
                            prompt_text = ""
                        assert prompt_text is not None
                        if request.max_tokens == 0:
                            # only return the prompt
                            delta_text = prompt_text
                            delta_token_ids = prompt_token_ids
                            out_logprobs = prompt_logprobs
                        else:
                            # echo the prompt and first token
                            delta_text = prompt_text + output.text
                            delta_token_ids = [
                                *prompt_token_ids,
                                *output.token_ids,
                            ]
                            out_logprobs = [
                                *(prompt_logprobs or []),
                                *(output.logprobs or []),
                            ]
                        prompt_token_ids_to_return = prompt_token_ids
                        has_echoed[i] = True
                    else:
                        # return just the delta
                        delta_text = output.text
                        delta_token_ids = output.token_ids
                        out_logprobs = output.logprobs

                        # has_echoed[i] is reused here to indicate whether
                        # we have already returned the prompt token IDs.
                        if not has_echoed[i] and request.return_token_ids:
                            prompt_token_ids_to_return = prompt_token_ids
                            has_echoed[i] = True

                        if (
                            not delta_text
                            and not delta_token_ids
                            and not previous_num_tokens[i]
                        ):
                            # Chunked prefill case, don't return empty chunks
                            continue

                    if request.logprobs is not None:
                        assert out_logprobs is not None, "Did not output logprobs"
                        logprobs = self._create_completion_logprobs(
                            token_ids=delta_token_ids,
                            top_logprobs=out_logprobs,
                            num_output_top_logprobs=request.logprobs,
                            tokenizer=tokenizer,
                            initial_text_offset=previous_text_lens[i],
                            return_as_token_id=request.return_tokens_as_token_ids,
                        )
                    else:
                        logprobs = None

                    previous_text_lens[i] += len(output.text)
                    previous_num_tokens[i] += len(output.token_ids)
                    finish_reason = output.finish_reason
                    stop_reason = output.stop_reason

                    self._raise_if_error(finish_reason, request_id)

                    chunk = CompletionStreamResponse(
                        id=request_id,
                        created=created_time,
                        model=model_name,
                        choices=[
                            CompletionResponseStreamChoice(
                                index=i,
                                text=delta_text,
                                logprobs=logprobs,
                                finish_reason=finish_reason,
                                stop_reason=stop_reason,
                                prompt_token_ids=prompt_token_ids_to_return,
                                token_ids=(
                                    as_list(output.token_ids)
                                    if request.return_token_ids
                                    else None
                                ),
                            )
                        ],
                    )
                    if include_continuous_usage:
                        prompt_tokens = num_prompt_tokens[prompt_idx]
                        completion_tokens = previous_num_tokens[i]
                        chunk.usage = UsageInfo(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens,
                        )

                    response_json = chunk.model_dump_json(exclude_unset=False)
                    yield f"data: {response_json}\n\n"

            total_prompt_tokens = sum(num_prompt_tokens)
            total_completion_tokens = sum(previous_num_tokens)
            final_usage_info = UsageInfo(
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=total_prompt_tokens + total_completion_tokens,
            )

            if self.enable_prompt_tokens_details and num_cached_tokens:
                final_usage_info.prompt_tokens_details = PromptTokenUsageInfo(
                    cached_tokens=num_cached_tokens
                )

            if include_usage:
                final_usage_chunk = CompletionStreamResponse(
                    id=request_id,
                    created=created_time,
                    model=model_name,
                    choices=[],
                    usage=final_usage_info,
                )
                final_usage_data = final_usage_chunk.model_dump_json(
                    exclude_unset=False, exclude_none=True
                )
                yield f"data: {final_usage_data}\n\n"

            # report to FastAPI middleware aggregate usage across all choices
            request_metadata.final_usage_info = final_usage_info

        except GenerationError as e:
            yield f"data: {self._convert_generation_error_to_streaming_response(e)}\n\n"
        except Exception as e:
            logger.exception("Error in completion stream generator.")
            data = self.create_streaming_error_response(e)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"