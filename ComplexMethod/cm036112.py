def _thinking_budget_validate(
    test_fakes: LogitsprocsTestFakes,
    persistent_batch: list[LogitsProcsRequestParams],
    logits_new: torch.Tensor,
    batch_index: int,
    request_params: LogitsProcsRequestParams,
    step_idx: int,
) -> None:
    """Validate thinking token budget processor behavior"""
    # Get the ThinkingTokenBudgetLogitsProcessor instance
    tb_processor: ThinkingTokenBudgetLogitsProcessor = next(
        test_fakes.get_logitsprocs_by_cls(ThinkingTokenBudgetLogitsProcessor)
    )

    # Get current request state
    state = tb_processor._state.get(batch_index)
    params = request_params.params

    # Validate thinking token budget configuration
    if hasattr(params, "thinking_token_budget") and params.thinking_token_budget:
        # State should exist for requests with thinking_token_budget
        if state is None:
            _raise_error_invalid(
                msg_suffix=(
                    f"Expected state for batch {batch_index} "
                    f"with thinking_token_budget={params.thinking_token_budget}"
                ),
                batch_index=batch_index,
                request_params=request_params,
                step_idx=step_idx,
            )

        # Validate budget matches what was set
        expected_budget = params.thinking_token_budget
        actual_budget = state["thinking_token_budget"]

        if actual_budget != expected_budget:
            _raise_error_invalid(
                msg_suffix=(
                    f"Budget mismatch: expected {expected_budget}, got {actual_budget}"
                ),
                batch_index=batch_index,
                request_params=request_params,
                step_idx=step_idx,
            )

        # Check if we're in thinking mode and validate token counting
        output_tokens = request_params.out_tokens

        # Find if thinking has started in output tokens
        thinking_started = False
        start_tokens = tb_processor.reasoning_start_token_ids

        if len(start_tokens) > 0:
            for i in range(len(output_tokens) - len(start_tokens) + 1):
                if output_tokens[i : i + len(start_tokens)] == start_tokens:
                    thinking_started = True
                    break

        if thinking_started:
            # If budget is exceeded, validate end token forcing
            think_count = state["think_count"]
            budget = state["thinking_token_budget"]

            if think_count >= budget:
                if not state["in_end"]:
                    _raise_error_invalid(
                        msg_suffix=(
                            f"Budget exceeded ({think_count} >= "
                            f"{budget}) but not "
                            "forcing end tokens"
                        ),
                        batch_index=batch_index,
                        request_params=request_params,
                        step_idx=step_idx,
                    )

                # Validate that only end tokens are allowed
                end_tokens = tb_processor.reasoning_end_token_ids
                if len(end_tokens) > 0:
                    expected_end_token_id = end_tokens[
                        min(state["end_count"], len(end_tokens) - 1)
                    ]

                    # Check logits masking
                    batch_logits = logits_new[batch_index]
                    for token_id in range(len(batch_logits)):
                        logit_value = batch_logits[token_id]

                        if token_id == expected_end_token_id:
                            # End token should not be masked
                            if logit_value == -float("inf"):
                                _raise_error_invalid(
                                    msg_suffix=(
                                        f"End token {token_id} should not be "
                                        "masked but is"
                                    ),
                                    batch_index=batch_index,
                                    request_params=request_params,
                                    step_idx=step_idx,
                                )
                        else:
                            # All other tokens should be masked when forcing end
                            if logit_value != -float("inf"):
                                _raise_error_invalid(
                                    msg_suffix=(
                                        f"Token {token_id} should be masked "
                                        f"when forcing end tokens, but "
                                        f"logit={logit_value}"
                                    ),
                                    batch_index=batch_index,
                                    request_params=request_params,
                                    step_idx=step_idx,
                                )