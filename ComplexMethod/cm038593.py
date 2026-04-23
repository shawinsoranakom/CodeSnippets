def request_output_to_completion_response(
        self,
        final_res_batch: list[RequestOutput],
        request: CompletionRequest,
        request_id: str,
        created_time: int,
        model_name: str,
        tokenizer: TokenizerLike | None,
        request_metadata: RequestResponseMetadata,
    ) -> CompletionResponse:
        choices: list[CompletionResponseChoice] = []
        num_prompt_tokens = 0
        num_generated_tokens = 0
        kv_transfer_params = None
        last_final_res = None
        for final_res in final_res_batch:
            last_final_res = final_res
            prompt_token_ids = final_res.prompt_token_ids
            assert prompt_token_ids is not None
            prompt_logprobs = clamp_prompt_logprobs(final_res.prompt_logprobs)
            prompt_text = final_res.prompt

            token_ids: GenericSequence[int]
            out_logprobs: GenericSequence[dict[int, Logprob] | None] | None

            for output in final_res.outputs:
                self._raise_if_error(output.finish_reason, request_id)

                assert request.max_tokens is not None
                if request.echo:
                    if request.return_token_ids:
                        prompt_text = ""
                    assert prompt_text is not None
                    if request.max_tokens == 0:
                        token_ids = prompt_token_ids
                        out_logprobs = prompt_logprobs
                        output_text = prompt_text
                    else:
                        token_ids = [*prompt_token_ids, *output.token_ids]

                        if request.logprobs is None:
                            out_logprobs = None
                        else:
                            assert prompt_logprobs is not None
                            assert output.logprobs is not None
                            out_logprobs = [
                                *prompt_logprobs,
                                *output.logprobs,
                            ]

                        output_text = prompt_text + output.text
                else:
                    token_ids = output.token_ids
                    out_logprobs = output.logprobs
                    output_text = output.text

                if request.logprobs is not None:
                    assert out_logprobs is not None, "Did not output logprobs"
                    logprobs = self._create_completion_logprobs(
                        token_ids=token_ids,
                        top_logprobs=out_logprobs,
                        tokenizer=tokenizer,
                        num_output_top_logprobs=request.logprobs,
                        return_as_token_id=request.return_tokens_as_token_ids,
                    )
                else:
                    logprobs = None

                choice_data = CompletionResponseChoice(
                    index=len(choices),
                    text=output_text,
                    logprobs=logprobs,
                    finish_reason=output.finish_reason,
                    stop_reason=output.stop_reason,
                    prompt_logprobs=final_res.prompt_logprobs,
                    prompt_token_ids=(
                        prompt_token_ids if request.return_token_ids else None
                    ),
                    token_ids=(
                        as_list(output.token_ids) if request.return_token_ids else None
                    ),
                )
                choices.append(choice_data)

                num_generated_tokens += len(output.token_ids)

            num_prompt_tokens += len(prompt_token_ids)

        usage = UsageInfo(
            prompt_tokens=num_prompt_tokens,
            completion_tokens=num_generated_tokens,
            total_tokens=num_prompt_tokens + num_generated_tokens,
        )

        if (
            self.enable_prompt_tokens_details
            and last_final_res
            and last_final_res.num_cached_tokens
        ):
            usage.prompt_tokens_details = PromptTokenUsageInfo(
                cached_tokens=last_final_res.num_cached_tokens
            )

        request_metadata.final_usage_info = usage
        if final_res_batch:
            kv_transfer_params = final_res_batch[0].kv_transfer_params
        return CompletionResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            choices=choices,
            usage=usage,
            kv_transfer_params=kv_transfer_params,
        )