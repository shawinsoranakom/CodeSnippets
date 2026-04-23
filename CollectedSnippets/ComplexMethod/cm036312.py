def test_parent_request_to_output_stream() -> None:
    parent_request = ParentRequest(make_request(SamplingParams(n=2)))
    parent_request.child_requests = {"child_id_0", "child_id_1"}
    output_0 = CompletionOutput(
        index=0, text="child 0", token_ids=[], cumulative_logprob=None, logprobs=None
    )
    output_1 = CompletionOutput(
        index=1, text="child 1", token_ids=[], cumulative_logprob=None, logprobs=None
    )
    # Request not finished
    assert ([output_0], False) == parent_request.get_outputs("child_id_0", output_0)
    assert ([output_1], False) == parent_request.get_outputs("child_id_1", output_1)
    assert ([output_0], False) == parent_request.get_outputs("child_id_0", output_0)
    assert ([output_1], False) == parent_request.get_outputs("child_id_1", output_1)

    # output_1 finished
    output_1.finish_reason = "ended"
    assert ([output_0], False) == parent_request.get_outputs("child_id_0", output_0)
    assert ([output_1], False) == parent_request.get_outputs("child_id_1", output_1)
    # Finished output_1 had already returned, DO NOT returned again
    assert ([output_0], False) == parent_request.get_outputs("child_id_0", output_0)
    assert parent_request.get_outputs("child_id_1", output_1) == ([], False)

    # output_0 finished
    output_0.finish_reason = "ended"
    assert ([output_0], True) == parent_request.get_outputs("child_id_0", output_0)
    assert parent_request.get_outputs("child_id_1", output_1) == ([], True)
    # Finished output_0 had already returned, DO NOT returned again
    assert parent_request.get_outputs("child_id_0", output_0) == ([], True)
    assert parent_request.get_outputs("child_id_1", output_1) == ([], True)