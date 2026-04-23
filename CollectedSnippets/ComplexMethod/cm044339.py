def test_debug_times():
    """ Test :class:`~lib.utils.DebugTimes` executes its logic correctly  """
    debug_times = DebugTimes()

    debug_times.step_start("Test1")
    time.sleep(0.1)
    debug_times.step_end("Test1")

    debug_times.step_start("Test2")
    time.sleep(0.2)
    debug_times.step_end("Test2")

    debug_times.step_start("Test1")
    time.sleep(0.1)
    debug_times.step_end("Test1")

    debug_times.summary()

    # Ensure that the summary method prints the min, mean, and max times for each step
    assert debug_times._display["min"] is True
    assert debug_times._display["mean"] is True
    assert debug_times._display["max"] is True

    # Ensure that the summary method includes the correct number of items for each step
    assert len(debug_times._times["Test1"]) == 2
    assert len(debug_times._times["Test2"]) == 1

    # Ensure that the summary method includes the correct min, mean, and max times for each step
    # Github workflow for macos-latest can swing out a fair way
    threshold = 2e-1 if platform.system() == "Darwin" else 1e-1
    assert min(debug_times._times["Test1"]) == pytest.approx(0.1, abs=threshold)
    assert min(debug_times._times["Test2"]) == pytest.approx(0.2, abs=threshold)
    assert max(debug_times._times["Test1"]) == pytest.approx(0.1, abs=threshold)
    assert max(debug_times._times["Test2"]) == pytest.approx(0.2, abs=threshold)
    assert (sum(debug_times._times["Test1"]) /
            len(debug_times._times["Test1"])) == pytest.approx(0.1, abs=threshold)
    assert (sum(debug_times._times["Test2"]) /
            len(debug_times._times["Test2"]) == pytest.approx(0.2, abs=threshold))