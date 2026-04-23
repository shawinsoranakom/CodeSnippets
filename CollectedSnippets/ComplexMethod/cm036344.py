def create_model_runner_output(
    reqs: list[Request],
    finished_sending: set[str] | None = None,
    finished_recving: set[str] | None = None,
    invalid_block_ids: set[int] | None = None,
    use_eos: bool = False,
    token_id: int = 0,
) -> ModelRunnerOutput:
    """Make dummy model runner output for testing."""

    # Make request data.
    req_ids = [req.request_id for req in reqs]
    req_id_to_index = {req_id: idx for idx, req_id in enumerate(req_ids)}

    # Make sampled tokens.
    sampled_token = EOS_TOKEN_ID if use_eos else token_id
    sampled_token_ids = [[sampled_token] for _ in req_ids]

    kv_connector_output = (
        None
        if (
            finished_sending is None
            and finished_recving is None
            and invalid_block_ids is None
        )
        else KVConnectorOutput(
            finished_sending=finished_sending,
            finished_recving=finished_recving,
            invalid_block_ids=invalid_block_ids or set(),
        )
    )

    # Make output data structure.
    return ModelRunnerOutput(
        req_ids=req_ids,
        req_id_to_index=req_id_to_index,
        sampled_token_ids=sampled_token_ids,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=None,
        kv_connector_output=kv_connector_output,
    )