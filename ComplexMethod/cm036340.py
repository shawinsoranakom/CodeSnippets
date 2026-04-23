async def test_cumulative_output_collector_n():
    """Test collector correctly handles multiple outputs by index."""
    collector = RequestOutputCollector(
        RequestOutputKind.CUMULATIVE, request_id="my-request-id-int"
    )
    outputs = [
        RequestOutput(
            request_id="my-request-id",
            prompt=None,
            prompt_token_ids=[1, 2, 3],
            prompt_logprobs=None,
            outputs=[
                CompletionOutput(
                    index=0,
                    text="a",
                    token_ids=[0],
                    cumulative_logprob=None,
                    logprobs=None,
                    finish_reason=None,
                ),
                CompletionOutput(
                    index=1,
                    text="b",
                    token_ids=[1],
                    cumulative_logprob=None,
                    logprobs=None,
                    finish_reason=None,
                ),
            ],
            finished=False,
        ),
        RequestOutput(
            request_id="my-request-id",
            prompt=None,
            prompt_token_ids=[1, 2, 3],
            prompt_logprobs=None,
            outputs=[
                CompletionOutput(
                    index=0,
                    text="ab",
                    token_ids=[0, 1],
                    cumulative_logprob=None,
                    logprobs=None,
                    finish_reason=None,
                ),
                CompletionOutput(
                    index=2,
                    text="c",
                    token_ids=[2],
                    cumulative_logprob=None,
                    logprobs=None,
                    finish_reason=None,
                ),
            ],
            finished=False,
        ),
    ]
    for output in outputs:
        collector.put(output)

    # Get the output and check that the text and token_ids are correct.
    result = await collector.get()
    # We are expecting
    # [{index: 0, text: "ab"}, {index: 1, text: "b"}, {index: 2, text: "c"}]
    assert len(result.outputs) == 3
    # First is the one where index is 0
    first = [k for k in result.outputs if k.index == 0]
    assert len(first) == 1
    assert first[0].text == "ab"

    # Second is the one where index is 1
    second = [k for k in result.outputs if k.index == 1]
    assert len(second) == 1
    assert second[0].text == "b"
    assert second[0].token_ids == [1]

    # Third is the one where index is 2
    third = [k for k in result.outputs if k.index == 2]
    assert len(third) == 1
    assert third[0].text == "c"