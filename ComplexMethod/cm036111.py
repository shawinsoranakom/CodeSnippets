def _min_tokens_validate(
    test_fakes: LogitsprocsTestFakes,
    persistent_batch: list[LogitsProcsRequestParams],
    logits_new: torch.Tensor,
    batch_index: int,
    request_params: LogitsProcsRequestParams,
    step_idx: int,
) -> None:
    """Validate min-tokens logitsproc applied correctly"""
    ref_num_out_tokens = len(request_params.out_tokens)
    min_reached = ref_num_out_tokens >= MIN_TOKENS_LEN_THRESHOLD
    ref_all_stop_token_ids = request_params.params.all_stop_token_ids
    mt_lp: MinTokensLogitsProcessor = next(
        test_fakes.get_logitsprocs_by_cls(MinTokensLogitsProcessor)
    )
    assert isinstance(mt_lp, MinTokensLogitsProcessor)
    min_tok = mt_lp.min_toks.get(batch_index, None)

    # Validate min-token logits processor state
    if min_tok:
        (_, out_tok, all_stop_token_ids) = min_tok
        num_out_tokens = len(out_tok)
        if num_out_tokens != ref_num_out_tokens:
            _raise_error_invalid(
                msg_suffix=(
                    "Number of output tokens in min-token logit processor "
                    f"request metadata ({num_out_tokens}) does not match "
                    f"reference ({ref_num_out_tokens})."
                ),
                batch_index=batch_index,
                request_params=request_params,
                step_idx=step_idx,
            )
        if ref_all_stop_token_ids != all_stop_token_ids:
            _raise_error_invalid(
                msg_suffix=(
                    "Stop token ids do not match reference; all_stop_token_ids: "
                    f"{sorted(all_stop_token_ids)}, ref_all_stop_token_ids: "
                    f"{sorted(ref_all_stop_token_ids)}"
                ),
                batch_index=batch_index,
                request_params=request_params,
                step_idx=step_idx,
            )
        if min_reached:
            _raise_error_invalid(
                msg_suffix=(
                    "Expected min-tokens request with min reached, but batch "
                    "index is recognized by min-tokens logits processor."
                ),
                batch_index=batch_index,
                request_params=request_params,
                step_idx=step_idx,
                err_cls=RuntimeError,
            )

    elif not min_reached:
        _raise_error_invalid(
            msg_suffix=(
                "Expected min-tokens request with min not reached, but batch "
                "index is not recognized by min-tokens logits processor."
            ),
            batch_index=batch_index,
            request_params=request_params,
            step_idx=step_idx,
            err_cls=RuntimeError,
        )

    # Validate min-token logits
    for token_id in range(VOCAB_SIZE):
        logits_for_token = logits_new[batch_index][token_id]
        if token_id in ref_all_stop_token_ids and not min_reached:
            if logits_for_token != -float("inf"):
                _raise_error_invalid(
                    msg_suffix=(
                        f"Token {token_id} is a stop token and "
                        "the sequence has not reached min length, "
                        "but the token is not masked "
                        f"(logit={logits_for_token})"
                    ),
                    batch_index=batch_index,
                    request_params=request_params,
                    step_idx=step_idx,
                )
        else:
            if logits_for_token == -float("inf"):
                _raise_error_invalid(
                    msg_suffix=(
                        f"Token {token_id} should not be masked but "
                        f"is (output len={ref_num_out_tokens})"
                    ),
                    batch_index=batch_index,
                    request_params=request_params,
                    step_idx=step_idx,
                )