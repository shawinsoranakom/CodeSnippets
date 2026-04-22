def require_widgets_deltas(
    runners: List[TestScriptRunner], timeout: float = 15
) -> None:
    """Wait for the given ScriptRunners to each produce the appropriate
    number of deltas for widgets_script.py before a timeout. If the timeout
    is reached, the runners will all be shutdown and an error will be thrown.
    """
    # widgets_script.py has 8 deltas, then a 1-delta loop. If 9
    # have been emitted, we can proceed with the test..
    NUM_DELTAS = 9

    t0 = time.time()
    num_complete = 0
    while time.time() - t0 < timeout:
        time.sleep(0.1)
        num_complete = sum(
            1 for runner in runners if len(runner.deltas()) >= NUM_DELTAS
        )
        if num_complete == len(runners):
            return

    # If we get here, at least 1 runner hasn't yet completed before our
    # timeout. Create an error string for debugging.
    err_string = f"require_widgets_deltas() timed out after {timeout}s ({num_complete}/{len(runners)} runners complete)"
    for runner in runners:
        if len(runner.deltas()) < NUM_DELTAS:
            err_string += f"\n- incomplete deltas: {runner.text_deltas()}"

    # Shutdown all runners before throwing an error, so that the script
    # doesn't hang forever.
    for runner in runners:
        runner.request_stop()
    for runner in runners:
        runner.join()

    raise RuntimeError(err_string)