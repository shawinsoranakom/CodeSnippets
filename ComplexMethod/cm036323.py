def test_engine_core():
    """Setup the EngineCore."""
    engine_args = EngineArgs(model=MODEL_NAME)
    vllm_config = engine_args.create_engine_config()
    executor_class = Executor.get_class(vllm_config)

    with set_default_torch_num_threads(1):
        engine_core = EngineCore(
            vllm_config=vllm_config, executor_class=executor_class, log_stats=True
        )
    """Test basic request lifecycle."""

    # First request.
    engine_core.add_request(*engine_core.preprocess_add_request(make_request()))
    assert len(engine_core.scheduler.waiting) == 1
    assert len(engine_core.scheduler.running) == 0

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 1

    # Second request.
    engine_core.add_request(*engine_core.preprocess_add_request(make_request()))
    assert len(engine_core.scheduler.waiting) == 1
    assert len(engine_core.scheduler.running) == 1

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 2

    # Add two requests in a row.
    engine_core.add_request(*engine_core.preprocess_add_request(make_request()))
    engine_core.add_request(*engine_core.preprocess_add_request(make_request()))
    assert len(engine_core.scheduler.waiting) == 2
    assert len(engine_core.scheduler.running) == 2

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 4

    # Loop through until they are all done.
    while (outs := engine_core.step_fn()[0].get(0)) and outs.outputs:
        pass

    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 0
    """Test abort cycle."""

    # Basic abort.
    req = make_request()
    request_id = req.request_id

    engine_core.add_request(*engine_core.preprocess_add_request(req))
    assert len(engine_core.scheduler.waiting) == 1
    assert len(engine_core.scheduler.running) == 0
    assert engine_core.scheduler.has_unfinished_requests()
    assert not engine_core.scheduler.has_finished_requests()

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 1
    assert engine_core.scheduler.has_unfinished_requests()
    assert not engine_core.scheduler.has_finished_requests()

    engine_core.abort_requests([request_id])
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 0
    assert not engine_core.scheduler.has_unfinished_requests()
    assert engine_core.scheduler.has_finished_requests()

    _ = engine_core.step_fn()
    assert not engine_core.scheduler.has_unfinished_requests()
    assert not engine_core.scheduler.has_finished_requests()

    # Add, step, abort 1 of the 3.
    req0 = make_request()
    req1 = make_request()
    req2 = make_request()

    engine_core.add_request(*engine_core.preprocess_add_request(req0))
    engine_core.add_request(*engine_core.preprocess_add_request(req1))
    assert len(engine_core.scheduler.waiting) == 2
    assert len(engine_core.scheduler.running) == 0

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 2

    engine_core.add_request(*engine_core.preprocess_add_request(req2))
    assert len(engine_core.scheduler.waiting) == 1
    assert len(engine_core.scheduler.running) == 2

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 3

    # Abort just one.
    engine_core.abort_requests([req1.request_id])
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 2

    _ = engine_core.step_fn()
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 2

    # Abort the other requests at the same time.
    engine_core.abort_requests([req2.request_id, req0.request_id])
    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 0

    # Sending duplicate requests with same request_id
    req0 = make_request()
    req1 = make_request()
    req0.request_id = req1.request_id = "test"
    engine_core.add_request(*engine_core.preprocess_add_request(req0))

    while engine_core.scheduler.has_requests():
        engine_core.step_fn()

    engine_core.add_request(*engine_core.preprocess_add_request(req1))
    while engine_core.scheduler.has_requests():
        engine_core.step_fn()

    assert len(engine_core.scheduler.waiting) == 0
    assert len(engine_core.scheduler.running) == 0