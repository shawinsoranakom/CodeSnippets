def test_wait_for_completion_or_failure(api_server_args):
    """Test that wait_for_completion_or_failure works with failures."""
    global WORKER_RUNTIME_SECONDS
    WORKER_RUNTIME_SECONDS = 1.0

    # Create the manager
    manager = APIServerProcessManager(**api_server_args)

    try:
        assert len(manager.processes) == 3

        # Create a result capture for the thread
        result: dict[str, Exception | None] = {"exception": None}

        def run_with_exception_capture():
            try:
                wait_for_completion_or_failure(api_server_manager=manager)
            except Exception as e:
                result["exception"] = e
            finally:
                manager.shutdown()

        # Start a thread to run wait_for_completion_or_failure
        wait_thread = threading.Thread(target=run_with_exception_capture, daemon=True)
        wait_thread.start()

        # Let all processes run for a short time
        time.sleep(0.2)

        # All processes should still be running
        assert all(proc.is_alive() for proc in manager.processes)

        # Now simulate a process failure
        print("Simulating process failure...")
        manager.processes[0].terminate()

        # Wait for the wait_for_completion_or_failure
        # to detect and handle the failure
        # This should trigger it to terminate all other processes
        wait_thread.join(timeout=1.0)

        # The wait thread should have exited
        assert not wait_thread.is_alive()

        # Verify that an exception was raised with appropriate error message
        assert result["exception"] is not None
        assert "died with exit code" in str(result["exception"])

        # All processes should now be terminated
        for i, proc in enumerate(manager.processes):
            assert not proc.is_alive(), f"Process {i} should not be alive"

    finally:
        manager.shutdown()
        time.sleep(0.2)