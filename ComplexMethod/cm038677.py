async def serve_tokens_full_generator(
        self,
        request: GenerateRequest,
        result_generator: AsyncGenerator[RequestOutput, None],
        request_id: str,
        model_name: str,
        request_metadata: RequestResponseMetadata,
    ) -> ErrorResponse | GenerateResponse:
        created_time = int(time.time())
        final_res: RequestOutput | None = None
        sampling_params: SamplingParams = request.sampling_params

        try:
            async for res in result_generator:
                final_res = res
        except asyncio.CancelledError:
            return self.create_error_response("Client disconnected")

        assert final_res is not None

        choices: list[GenerateResponseChoice] = []
        num_generated_tokens = 0
        for output in final_res.outputs:
            token_ids = output.token_ids
            out_logprobs = output.logprobs

            # This is top_logprobs in completions API
            if sampling_params.logprobs is not None:
                assert out_logprobs is not None, "Did not output logprobs"
                logprobs = self._create_tokens_logprobs(
                    token_ids=token_ids,
                    top_logprobs=out_logprobs,
                    num_output_top_logprobs=sampling_params.logprobs,
                )
            else:
                logprobs = None

            choice_data = GenerateResponseChoice(
                index=output.index,
                logprobs=logprobs,
                finish_reason=output.finish_reason if output.finish_reason else "stop",
                token_ids=as_list(output.token_ids),
            )

            choices.append(choice_data)
            num_generated_tokens += len(output.token_ids)

        assert final_res.prompt_token_ids is not None
        num_prompt_tokens = len(final_res.prompt_token_ids)
        if final_res.encoder_prompt_token_ids is not None:
            num_prompt_tokens += len(final_res.encoder_prompt_token_ids)

        usage = UsageInfo(
            prompt_tokens=num_prompt_tokens,
            completion_tokens=num_generated_tokens,
            total_tokens=num_prompt_tokens + num_generated_tokens,
        )
        if self.enable_prompt_tokens_details and final_res.num_cached_tokens:
            # This info is not available at the /coordinator level
            usage.prompt_tokens_details = PromptTokenUsageInfo(
                cached_tokens=final_res.num_cached_tokens
            )

        request_metadata.final_usage_info = usage

        response = GenerateResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            choices=choices,
            usage=usage,
            prompt_logprobs=clamp_prompt_logprobs(final_res.prompt_logprobs),
            kv_transfer_params=final_res.kv_transfer_params,
        )

        # Log complete response if output logging is enabled
        if self.enable_log_outputs and self.request_logger:
            for choice in choices:
                # Get the corresponding output token IDs
                output_token_ids = None
                if choice.index < len(final_res.outputs):
                    output_token_ids = final_res.outputs[choice.index].token_ids

                if output_token_ids:
                    # Log token_ids only.
                    self.request_logger.log_outputs(
                        request_id=request_id,
                        outputs="",
                        output_token_ids=output_token_ids,
                        finish_reason=choice.finish_reason,
                        is_streaming=False,
                        delta=False,
                    )

        return response