def _validate_logprobs(
    gen_tokens: dict[str, list[int]],
    gen_logprobs: dict[str, SampleLogprobs | None],
    gen_prompt_logprobs: dict[str, PromptLogprobs | None],
    gen_cumulative_logprob: dict[str, float],
    dtv: DummyOutputProcessorTestVectors,
    request_id_list: list[str],
    num_sample_logprobs: int | None,
    num_prompt_logprobs: int | None,
) -> None:
    for req_idx, req_id in enumerate(request_id_list):
        new_tokens = gen_tokens[req_id]
        logprobs = gen_logprobs[req_id]
        prompt_logprobs = gen_prompt_logprobs[req_id]
        cumulative_logprob = gen_cumulative_logprob[req_id]
        prompt_token_ids = dtv.prompt_tokens[req_idx]
        ref_logprobs = dtv.generation_logprobs[req_idx]
        ref_prompt_logprobs = dtv.prompt_logprobs[req_idx]
        if num_sample_logprobs is not None:
            # Validate sample logprobs
            assert logprobs is not None, (
                f"Request {req_id} requires sample"
                " logprobs but sample logprobs are"
                " None."
            )
            # Require num sampled tokens to match num
            # sampled logprobs - especially important
            # to check since the detokenizer can cause
            # a request to finish early due to a stop
            # string being hit
            num_new_tokens = len(new_tokens)
            len_sample_logprobs = len(logprobs)
            assert num_new_tokens == len_sample_logprobs, (
                f"Request {req_id} has {num_new_tokens}"
                " completion tokens but has"
                f" {len_sample_logprobs} sample logprobs."
            )
            ref_cumulative_logprob = 0.0
            for idx, (sampled_token, pos_logprob_dict) in enumerate(
                zip(new_tokens, logprobs)
            ):
                # Break out the reference log probability value &
                # logprob token id tensors associated with this
                # position in the completion. Also break out the
                # sampled token ranks
                (ref_pos_logprob_toks, ref_pos_logprob_vals, ref_sampled_token_rank) = (
                    ref_logprobs[idx]
                )
                # For each position in the completion sequence,
                # ensure the actual sampled token is among the
                # logprobs
                assert sampled_token in pos_logprob_dict, (
                    f"Sampled token {sampled_token} not"
                    f" present in logprob at index {idx}"
                )

                # Validate number of sample logprobs
                num_lp_toks = len(pos_logprob_dict)
                assert (
                    num_lp_toks == num_sample_logprobs
                    or num_lp_toks == num_sample_logprobs + 1
                ), (
                    "Valid numbers of sample logprobs are"
                    f" {num_sample_logprobs} or"
                    f" {num_sample_logprobs + 1} but"
                    f" {num_lp_toks} logprobs found at"
                    f" position {idx}. Logprobs dict:"
                    f" {pos_logprob_dict}"
                )

                # Validate sampled token logprob rank
                smp_lp = pos_logprob_dict[sampled_token]
                smp_lp_rank = smp_lp.rank
                assert ref_sampled_token_rank == smp_lp_rank, (
                    "Sampled token logprob rank"
                    f" {smp_lp_rank} does not match"
                    " correct value"
                    f" {ref_sampled_token_rank}"
                    f" in Logprob {smp_lp}"
                )

                # Validate that the logprob processor yields
                # the correct log probabilities and valid
                # rankings
                rank_one_appears = False
                for jdx in range(1, len(ref_pos_logprob_toks)):
                    # Iterate over the (logprob val,logprob tok id)
                    # pairs expected by the test fixture at this
                    # position in the completion.
                    ref_lp_val = ref_pos_logprob_vals[jdx]
                    ref_tok_id = ref_pos_logprob_toks[jdx]
                    assert ref_tok_id in pos_logprob_dict, (
                        f"Expected token {ref_tok_id} to be"
                        f" in logprob dict but it is not."
                    )

                    # Extract actually-generated logprob
                    # info
                    lp = pos_logprob_dict[ref_tok_id]
                    lp_val = lp.logprob
                    lp_rank = lp.rank

                    # A "top" (rank 1) logprob must be
                    # present
                    rank_one_appears = True if lp_rank == 1 else rank_one_appears

                    # Rank must be >= 1
                    assert lp_rank >= 1, (
                        f"Logprob {lp} has invalid"
                        f" rank {lp_rank} < 1."
                        f" Logprob dict: {pos_logprob_dict}"
                    )

                    # Validate log probability
                    assert math.isclose(lp_val, ref_lp_val), (
                        f"Token id {ref_tok_id} appears in logprobs dict"
                        f" at position {idx} in completion with log"
                        f" probability {lp_val} but {ref_lp_val} was"
                        f" expected. Logprob: {lp}"
                    )

                assert rank_one_appears, (
                    f"No Logprob has rank 1"
                    " in the following Logprob"
                    f" dict: {pos_logprob_dict}"
                )

                # Validate logprobs detokenization
                for lp_tok in pos_logprob_dict:
                    # Confirm that sample logprob decoded token matches
                    # the logprob token id at this sequence position
                    decoded_token = pos_logprob_dict[lp_tok].decoded_token
                    ref_decoded_token = _ref_convert_id_to_token(dtv.tokenizer, lp_tok)

                    # With UTF-8 correction logic, tokens ending with "�"
                    # (incomplete byte sequences) are corrected to either
                    # empty string or proper UTF-8 characters
                    if ref_decoded_token.endswith("�"):
                        # Token needs UTF-8 correction
                        assert not decoded_token.endswith("�"), (
                            f"Sampled logprob token id {lp_tok} decodes to"
                            f" '{ref_decoded_token}' (ends with replacement char)"
                            f" but corrected decoded token '{decoded_token}'"
                            f" still ends with replacement char"
                            f" (at position {idx}). UTF-8 correction should"
                            f" have removed it."
                        )
                    else:
                        # No correction needed, should match exactly
                        assert decoded_token == ref_decoded_token, (
                            f"Sampled logprob token id {lp_tok} decodes to"
                            f" {ref_decoded_token} but Logprob decoded"
                            f" token is {decoded_token} instead"
                            f" (at position {idx})"
                        )

                ref_cumulative_logprob += pos_logprob_dict[sampled_token].logprob
            # Assert that cumulative logprobs are correct
            assert math.isclose(cumulative_logprob, ref_cumulative_logprob)
        else:
            # Sample logprobs disabled for this request
            assert logprobs is None
            assert cumulative_logprob is None

        if num_prompt_logprobs is not None:
            # Validate prompt logprobs
            assert prompt_logprobs is not None, (
                f"Request {req_id} requires prompt"
                " logprobs but prompt logprobs are"
                " None."
            )
            # Require num prompt tokens to match num
            # prompt logprobs
            num_prompt_tokens = len(prompt_token_ids)
            len_prompt_logprobs = len(prompt_logprobs)
            assert num_prompt_tokens == len_prompt_logprobs, (
                f"Request {req_id} has {num_prompt_tokens}"
                " prompt tokens but has"
                f" {len_prompt_logprobs} prompt logprobs."
            )
            # First prompt logprob is None
            first_plp_dict = prompt_logprobs[0]
            assert first_plp_dict is None, (
                f"Request {req_id} first prompt logprob"
                f" should be None but has following value"
                f" instead: {first_plp_dict}"
            )
            # Break out the reference prompt log prob value &
            # logprob token id matrices for the whole prompt.
            # Also break out the prompt token rank vector
            (
                ref_prompt_logprob_toks,
                ref_prompt_logprob_vals,
                ref_prompt_token_ranks,
                _,
            ) = ref_prompt_logprobs
            for idx, (prompt_token, pos_logprob_dict) in enumerate(
                zip(prompt_token_ids[1:], prompt_logprobs[1:])
            ):
                # Break out the reference prompt log prob value
                # vector, prompt logprob token id vector, and
                # prompt token rank at the current position.
                (
                    ref_pos_prompt_logprob_toks,
                    ref_pos_prompt_logprob_vals,
                    ref_pos_prompt_token_rank,
                ) = (
                    ref_prompt_logprob_toks[idx, :],
                    ref_prompt_logprob_vals[idx, :],
                    ref_prompt_token_ranks[idx],
                )

                # For each position in the prompt sequence,
                # ensure the actual prompt token is among the
                # logprobs
                assert prompt_token in pos_logprob_dict, (
                    f"Prompt token {prompt_token} not present in logprob at index {idx}"
                )
                # Validate number of prompt logprobs
                num_plp_toks = len(pos_logprob_dict)
                assert (
                    num_plp_toks == num_prompt_logprobs
                    or num_plp_toks == num_prompt_logprobs + 1
                ), (
                    "Valid numbers of prompt logprobs are"
                    f" {num_prompt_logprobs} or"
                    f" {num_prompt_logprobs + 1} but"
                    f" {num_plp_toks} logprobs found at"
                    f" position {idx}. Logprobs dict:"
                    f" {pos_logprob_dict}"
                )

                # Validate prompt token logprob rank
                prmpt_tok_lp = pos_logprob_dict[prompt_token]
                prmpt_tok_lp_rank = prmpt_tok_lp.rank
                ref_prmpt_tok_lp_rank = ref_pos_prompt_token_rank
                assert ref_prmpt_tok_lp_rank == prmpt_tok_lp_rank, (
                    "Prompt token logprob rank"
                    f" {prmpt_tok_lp_rank} does not match"
                    " correct value"
                    f" {ref_prmpt_tok_lp_rank}"
                    f" in Logprob {prmpt_tok_lp}"
                )

                # Validate that the logprob processor yields
                # the correct prompt log probs and valid
                # rankings
                rank_one_appears = False
                for jdx in range(1, len(ref_pos_prompt_logprob_toks)):
                    # Iterate over the (logprob val,logprob tok id)
                    # pairs expected by the test fixture at this
                    # position in the completion.
                    ref_plp_val = float(ref_pos_prompt_logprob_vals[jdx])
                    ref_tok_id = int(ref_pos_prompt_logprob_toks[jdx])
                    assert ref_tok_id in pos_logprob_dict, (
                        f"Expected token {ref_tok_id} to be"
                        f" in logprob dict but it is not."
                    )

                    # Extract actually-generated logprob
                    # info
                    plp = pos_logprob_dict[ref_tok_id]
                    plp_val = plp.logprob
                    plp_rank = plp.rank

                    # A "top" (rank 1) logprob must be
                    # present
                    rank_one_appears = True if plp_rank == 1 else rank_one_appears

                    # Rank must be >= 1
                    assert plp_rank >= 1, (
                        f"Logprob {plp} has invalid"
                        f" rank {plp_rank} < 1."
                        f" Logprob dict: {pos_logprob_dict}"
                    )

                    # Validate log probability
                    assert math.isclose(plp_val, ref_plp_val), (
                        f"Token id {ref_tok_id} appears in logprobs dict"
                        f" at position {idx} in completion with log"
                        f" probability {plp_val} but {ref_plp_val} was"
                        f" expected. Logprob: {plp}"
                    )

                assert rank_one_appears, (
                    f"No Logprob has rank 1"
                    " in the following Logprob"
                    f" dict: {pos_logprob_dict}"
                )

                # Validate prompt logprob detokenization
                for plp_tok in pos_logprob_dict:
                    # Confirm that prompt logprob decoded token matches
                    # the logprob token id at this sequence position
                    decoded_token = pos_logprob_dict[plp_tok].decoded_token
                    ref_decoded_token = _ref_convert_id_to_token(dtv.tokenizer, plp_tok)

                    # With UTF-8 correction logic, tokens ending with "�"
                    # (incomplete byte sequences) are corrected to either
                    # empty string or proper UTF-8 characters
                    if ref_decoded_token.endswith("�"):
                        # Token needs UTF-8 correction
                        assert not decoded_token.endswith("�"), (
                            f"Prompt logprob token id {plp_tok} decodes to"
                            f" '{ref_decoded_token}' (ends with replacement char)"
                            f" but corrected decoded token '{decoded_token}'"
                            f" still ends with replacement char"
                            f" (at position {idx}). UTF-8 correction should"
                            f" have removed it."
                        )
                    else:
                        # No correction needed, should match exactly
                        assert decoded_token == ref_decoded_token, (
                            f"Prompt logprob token id {plp_tok} decodes to"
                            f" {ref_decoded_token} but Logprob decoded"
                            f" token is {decoded_token} instead"
                            f" (at position {idx})"
                        )
        else:
            # Prompt logprobs disabled for this request
            assert prompt_logprobs is None