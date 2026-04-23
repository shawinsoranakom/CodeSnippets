def _run_and_validate(
    vllm_model: VllmRunner,
    test_prompts: list[str],
    vllm_sampling_params: SamplingParams,
    hf_logprobs: list[list[torch.Tensor]],
    hf_outputs: list[tuple[list[int], str]],
    logprob_prompt_logprob_list: BatchLogprobsSpecType,
    temperature: float,
    max_tokens: int,
    do_apc: bool,
) -> None:
    vllm_results = vllm_model.llm.generate(
        test_prompts, sampling_params=vllm_sampling_params
    )

    for vllm_result, hf_logprob, hf_output, logprob_prompt_logprob in zip(
        vllm_results, hf_logprobs, hf_outputs, logprob_prompt_logprob_list
    ):
        # Extract request-level (prompt)logprobs config
        num_top_logprobs, num_top_prompt_logprobs = logprob_prompt_logprob

        # Test whether sampled token output is consistent between vLLM and HF
        # vLLM prompt+completion should match HF output
        if temperature == 0.0:
            assert (
                vllm_result.prompt_token_ids + vllm_result.outputs[0].token_ids
                == hf_output[0]
            )
        else:
            # Sampled tokens won't match if not greedy
            assert (
                vllm_result.prompt_token_ids
                == hf_output[0][: len(vllm_result.prompt_token_ids)]
            )

        # Validate sample logprobs
        if num_top_logprobs is not None:
            assert num_top_logprobs is not None
            # Confirm that the structure of the sample logprobs in the result is
            # correct
            assert vllm_result.outputs[0].logprobs is not None
            assert len(vllm_result.outputs[0].logprobs) == max_tokens
            for logprobs, token_id in zip(
                vllm_result.outputs[0].logprobs, vllm_result.outputs[0].token_ids
            ):
                assert logprobs is not None

                # Confirm that the output token appears among the logprobs
                assert token_id in logprobs
                token_in_topk = logprobs[token_id].rank <= num_top_logprobs

                # If the output token is not included in the top K
                # logprob, it can return 1 more data
                if token_in_topk and num_top_logprobs != 0:
                    assert len(logprobs) == num_top_logprobs
                else:
                    assert len(logprobs) == num_top_logprobs + 1

                if num_top_logprobs > 0:
                    # We should have an entry for each of the topk ranks
                    all_ranks = {lp.rank for lp in logprobs.values()}
                    assert all(r in all_ranks for r in range(1, num_top_logprobs + 1))

            output_text = vllm_result.outputs[0].text
            output_string_from_most_likely_tokens_lst: list[str] = []
            for top_logprobs in vllm_result.outputs[0].logprobs:
                top_logprob = next(iter(top_logprobs.values()))
                output_string_from_most_likely_tokens_lst.append(
                    top_logprob.decoded_token
                )

            output_string_from_most_likely_tokens = "".join(
                output_string_from_most_likely_tokens_lst
            )
            assert_incr_detok_str_matches_non_incr_detok_str(
                output_text,
                output_string_from_most_likely_tokens,
                "The output text from the top logprob for each token "
                "position should be the same as the output text in the "
                "result.",
            )

            # Compare vLLM sample logprobs to HF
            vllm_sample_logprobs = vllm_result.outputs[0].logprobs
            for i, top_logprobs in enumerate(vllm_sample_logprobs):
                for token_id, sample_logprob in top_logprobs.items():
                    if temperature == 0.0 or i == 0:
                        logprob = sample_logprob.logprob
                        torch.testing.assert_close(
                            logprob,
                            hf_logprob[i][-1][token_id].item(),
                            atol=1e-2,
                            rtol=1e-2,
                        )
                    assert isinstance(sample_logprob.decoded_token, str), (
                        "The token should be decoded by the time it is"
                        " returned to the user."
                    )

            # At this point we know the sample logprobs are correct for this
            # request. Validate that cumulative_logprob is actually the sum.
            # For each request, assert that the returned cumulative logprob
            # matches the correct value, which is computed below.
            torch.testing.assert_close(
                vllm_result.outputs[0].cumulative_logprob,
                compute_correct_cumulative_logprob(vllm_result.outputs[0]),
                atol=1e-6,
                rtol=1e-6,
            )
        else:
            # Logprobs disabled for this request; should be None
            assert vllm_result.outputs[0].logprobs is None

        # Validate prompt logprobs
        if num_top_prompt_logprobs is not None:
            # Confirm that structure of prompt logprobs in result is correct
            assert vllm_result.prompt_logprobs is not None
            # - The first prompt logprob is always None
            assert vllm_result.prompt_logprobs[0] is None
            # - Prompt logprobs are returned for all indices in
            #   the prompt
            assert len(vllm_result.prompt_logprobs) == len(vllm_result.prompt_token_ids)
            for prompt_logprobs, prompt_token_id in zip(
                vllm_result.prompt_logprobs[1:], vllm_result.prompt_token_ids[1:]
            ):
                assert prompt_logprobs is not None

                # Confirm that the prompt token appears among the logprobs
                assert prompt_token_id in prompt_logprobs
                token_in_topk = (
                    prompt_logprobs[prompt_token_id].rank <= num_top_prompt_logprobs
                )

                # If the prompt token is not included in the top K
                # logprob, it can return 1 more data
                if token_in_topk and num_top_prompt_logprobs != 0:
                    assert len(prompt_logprobs) == num_top_prompt_logprobs
                else:
                    assert len(prompt_logprobs) == num_top_prompt_logprobs + 1

                if num_top_prompt_logprobs > 0:
                    # We should have an entry for each of the topk ranks
                    all_ranks = {lp.rank for lp in prompt_logprobs.values()}
                    assert all(
                        r in all_ranks for r in range(1, num_top_prompt_logprobs + 1)
                    )

            # Compare prompt logprobs to HF
            # The first prompt logprob is always None, so we compare it from
            # 1:.
            vllm_prompt_logprobs = vllm_result.prompt_logprobs[1:]
            for i, vllm_prompt_logprob_dict in enumerate(vllm_prompt_logprobs):
                for token_id, logprob in vllm_prompt_logprob_dict.items():
                    torch.testing.assert_close(
                        logprob.logprob,
                        hf_logprob[0][i][token_id].item(),
                        atol=2e-2,
                        rtol=2e-2,
                    )
        else:
            assert vllm_result.prompt_logprobs is None