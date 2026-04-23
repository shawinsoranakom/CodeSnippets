def _assert_right_encoder_inputs(
    output: SchedulerOutput,
    check_exist: bool | None = True,
    requests: list[Request] | None = None,
    expected_encoder_inputs: list[list[int]] | None = None,
    expected_total_reqs: int | None = None,
):
    """Verify that requests/mm_hashes should (not) in scheduled encoder input
    If check_exist is False, this function returns True
    if requests are NOT in encoder inputs"""

    # Get the scheduled encoder inputs
    # NOTE: scheduled_encoder_inputs is a dictionary with request id as key
    scheduled_encoder_inputs = output.scheduled_encoder_inputs

    # Check if scheduled_encoder_inputs is empty as expected
    if expected_total_reqs is not None:
        assert len(scheduled_encoder_inputs) == expected_total_reqs
        if expected_total_reqs == 0:
            return

    # Number of expected encoder inputs should match number of requests
    if expected_encoder_inputs:
        assert check_exist and requests is not None  # only support expect input exist
        assert len(requests) == len(expected_encoder_inputs)

    # Check request (not) exist as expected
    for i, request in enumerate(requests if requests is not None else []):
        assert (request.request_id in scheduled_encoder_inputs) is check_exist, (
            f"Request {request.id} presence mismatch: expected {check_exist}, "
            f"got {request.id in scheduled_encoder_inputs}"
        )
        if expected_encoder_inputs:
            scheduled_encoder_input = scheduled_encoder_inputs[request.request_id]
            assert scheduled_encoder_input == expected_encoder_inputs[i]