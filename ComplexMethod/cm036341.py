def test_abort_requests(runner: str, abort_by: str, dummy_test_vectors):
    output_processor = OutputProcessor(dummy_test_vectors.tokenizer, log_stats=True)
    requests = [
        EngineCoreRequest(
            request_id=f"request-{idx}",
            external_req_id=f"external-{idx}",
            prompt_token_ids=prompt_tokens,
            mm_features=None,
            arrival_time=0,
            lora_request=None,
            cache_salt=None,
            data_parallel_rank=None,
            sampling_params=SamplingParams() if runner == "generate" else None,
            pooling_params=PoolingParams(task="embed") if runner == "pooling" else None,
        )
        for idx, prompt_tokens in enumerate(dummy_test_vectors.prompt_tokens)
    ]

    for request in requests:
        if runner == "generate":
            output_kind = request.sampling_params.output_kind
        else:
            output_kind = request.pooling_params.output_kind
        queue = RequestOutputCollector(
            output_kind=output_kind, request_id=request.request_id
        )
        output_processor.add_request(request, None, queue=queue)

    for request in requests:
        if abort_by == "internal":
            output_processor.abort_requests([request.request_id], internal=True)
        else:
            output_processor.abort_requests([request.external_req_id], internal=False)