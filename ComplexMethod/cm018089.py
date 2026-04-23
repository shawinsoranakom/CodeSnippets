def verify_cleanup(
    expected_lingering_tasks: bool,
    expected_lingering_timers: bool,
) -> Generator[None]:
    """Verify that the test has cleaned up resources correctly.

    This fixture requires the event loop to be stopped.
    It therefore cannot be an async fixture.

    Use @pytest_asyncio.fixture to make sure the correct event loop is set
    regardless before calling the fixture.
    """
    event_loop = asyncio.get_event_loop()
    threads_before = frozenset(threading.enumerate())
    tasks_before = asyncio.all_tasks(event_loop)
    yield

    event_loop.run_until_complete(event_loop.shutdown_default_executor())

    if len(INSTANCES) >= 2:
        count = len(INSTANCES)
        for inst in INSTANCES:
            inst.stop()
        pytest.exit(f"Detected non stopped instances ({count}), aborting test run")

    # Warn and clean-up lingering tasks and timers
    # before moving on to the next test.
    tasks = asyncio.all_tasks(event_loop) - tasks_before
    for task in tasks:
        if expected_lingering_tasks:
            _LOGGER.warning("Lingering task after test %r", task)
        else:
            pytest.fail(f"Lingering task after test {task!r}")
        task.cancel()
    if tasks:
        event_loop.run_until_complete(asyncio.wait(tasks))

    for handle in get_scheduled_timer_handles(event_loop):
        if not handle.cancelled():
            with long_repr_strings():
                if expected_lingering_timers:
                    _LOGGER.warning("Lingering timer after test %r", handle)
                elif handle._args and isinstance(job := handle._args[-1], HassJob):
                    if job.cancel_on_shutdown:
                        continue
                    pytest.fail(f"Lingering timer after job {job!r}")
                else:
                    pytest.fail(f"Lingering timer after test {handle!r}")
                handle.cancel()

    # Verify no threads where left behind.
    threads = frozenset(threading.enumerate()) - threads_before
    for thread in threads:
        assert (
            isinstance(thread, threading._DummyThread)
            or thread.name.startswith("waitpid-")
            or "_run_safe_shutdown_loop" in thread.name
        )

    try:
        # Verify the default time zone has been restored
        assert dt_util.DEFAULT_TIME_ZONE is datetime.UTC
    finally:
        # Restore the default time zone to not break subsequent tests
        dt_util.DEFAULT_TIME_ZONE = datetime.UTC

    try:
        # Verify respx.mock has been cleaned up
        assert not respx.mock.routes, (
            "respx.mock routes not cleaned up, maybe the test needs to be decorated with @respx.mock"
        )
    finally:
        # Clear mock routes not break subsequent tests
        respx.mock.clear()

    try:
        # Verify no socket connections were attempted
        assert not HASocketBlockedError.instances, "the test opens sockets"
    except AssertionError:
        for instance in HASocketBlockedError.instances:
            _LOGGER.exception("Socket opened during test", exc_info=instance)
        raise
    finally:
        # Reset socket connection instance count to not break subsequent tests
        HASocketBlockedError.instances = []