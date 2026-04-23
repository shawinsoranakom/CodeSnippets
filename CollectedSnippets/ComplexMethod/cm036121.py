def test_reorder_batch_to_split_decodes_and_prefills(test_case: ReorderTestCase):
    req_ids = [f"r{i}" for i in range(len(test_case.requests))]
    num_computed_tokens = np.array([r[1] for r in test_case.requests], dtype=np.int32)
    num_scheduled_tokens = {f"r{i}": r[0] for i, r in enumerate(test_case.requests)}
    num_prompt_tokens = np.array([r[2] for r in test_case.requests], dtype=np.int32)

    input_batch = MockInputBatch(req_ids, num_computed_tokens, num_prompt_tokens)
    scheduler_output = MockSchedulerOutput(num_scheduled_tokens)

    modified = reorder_batch_to_split_decodes_and_prefills(
        input_batch, scheduler_output, decode_threshold=test_case.decode_threshold
    )

    expected_req_ids = [f"r{i}" for i in test_case.expected_order]

    assert modified == test_case.expected_modified, (
        f"Expected modified={test_case.expected_modified}, got {modified}"
    )
    assert input_batch.req_ids == expected_req_ids, (
        f"Expected order {expected_req_ids}, got {input_batch.req_ids}"
    )