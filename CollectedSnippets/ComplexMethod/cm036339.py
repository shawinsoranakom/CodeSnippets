async def test_request_output_collector():
    NUM_REQS = 3
    TEXT = "a"

    def make_outputs() -> list[RequestOutput]:
        return [
            RequestOutput(
                request_id="my-request-id",
                prompt=None,
                prompt_token_ids=[1, 2, 3],
                prompt_logprobs=None,
                outputs=[
                    CompletionOutput(
                        index=0,
                        text=TEXT,
                        token_ids=[idx],
                        cumulative_logprob=(idx + 1 * 1.0),
                        logprobs=[{"a": idx, "b": idx}],
                        finish_reason="length" if (idx == NUM_REQS - 1) else None,
                    )
                ],
                finished=(idx == NUM_REQS - 1),
            )
            for idx in range(NUM_REQS)
        ]

    collector = RequestOutputCollector(
        RequestOutputKind.DELTA, request_id="my-request-id-int"
    )

    # CASE 1: Put then get.
    outputs = make_outputs()
    collector.put(outputs[0])
    output = await collector.get()
    assert not collector.ready.is_set()
    assert collector.output is None
    assert output.outputs[0].text == "a"
    assert output.outputs[0].token_ids == [0]

    # CASE 2: 2 puts then get.
    num_to_put = 2
    outputs = make_outputs()
    for i in range(num_to_put):
        collector.put(outputs[i])
    output = await collector.get()
    assert not collector.ready.is_set()
    assert collector.output is None

    assert not output.finished
    # Text, token_ids, and logprobs should get merged.
    assert output.outputs[0].text == TEXT * num_to_put
    for tok_0, tok_1 in zip(output.outputs[0].token_ids, list(range(num_to_put))):
        assert tok_0 == tok_1
    assert len(output.outputs[0].logprobs) == num_to_put

    # Cumulative logprobs should be the last one.
    cumulative_logprob_expected = 1.0 * num_to_put
    assert output.outputs[0].cumulative_logprob == cumulative_logprob_expected

    # CASE 3: Put all 3 (including a finished).
    num_to_put = 3
    outputs = make_outputs()
    for i in range(num_to_put):
        collector.put(outputs[i])
    output = await collector.get()
    assert not collector.ready.is_set()
    assert collector.output is None

    assert output.finished
    assert output.outputs[0].finish_reason == "length"
    # Text, token_ids, and logprobs should get merged.
    assert output.outputs[0].text == TEXT * num_to_put
    for tok_0, tok_1 in zip(output.outputs[0].token_ids, list(range(num_to_put))):
        assert tok_0 == tok_1
    assert len(output.outputs[0].logprobs) == num_to_put

    # Cumulative logprobs should be the last one.
    cumulative_logprob_expected = 1.0 * num_to_put
    assert output.outputs[0].cumulative_logprob == cumulative_logprob_expected