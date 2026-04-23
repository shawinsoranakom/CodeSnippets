def test_external_process_monitoring(api_server_args):
    """Test that wait_for_completion_or_failure handles additional processes."""
    global WORKER_RUNTIME_SECONDS
    WORKER_RUNTIME_SECONDS = 100

    # Create and start the external process
    # (simulates local_engine_manager or coordinator)
    spawn_context = multiprocessing.get_context("spawn")
    external_proc = spawn_context.Process(
        target=mock_run_api_server_worker, name="MockExternalProcess"
    )
    external_proc.start()

    # Create the class to simulate a coordinator
    class MockCoordinator:
        def __init__(self, proc):
            self.proc = proc

        def shutdown(self):
            if self.proc.is_alive():
                self.proc.terminate()
                self.proc.join(timeout=0.5)

    # Create a mock coordinator with the external process
    mock_coordinator = MockCoordinator(external_proc)

    # Create the API server manager
    manager = APIServerProcessManager(**api_server_args)

    try:
        # Verify manager initialization
        assert len(manager.processes) == 3

        # Create a result capture for the thread
        result: dict[str, Exception | None] = {"exception": None}

        def run_with_exception_capture():
            try:
                wait_for_completion_or_failure(
                    api_server_manager=manager, coordinator=mock_coordinator
                )
            except Exception as e:
                result["exception"] = e
            finally:
                manager.shutdown()
                mock_coordinator.shutdown()

        # Start a thread to run wait_for_completion_or_failure
        wait_thread = threading.Thread(target=run_with_exception_capture, daemon=True)
        wait_thread.start()

        # Terminate the external process to trigger a failure
        time.sleep(0.2)
        external_proc.terminate()

        # Wait for the thread to detect the failure
        wait_thread.join(timeout=1.0)

        # The wait thread should have completed
        assert not wait_thread.is_alive(), (
            "wait_for_completion_or_failure thread still running"
        )

        # Verify that an exception was raised with appropriate error message
        assert result["exception"] is not None, "No exception was raised"
        error_message = str(result["exception"])
        assert "died with exit code" in error_message, (
            f"Unexpected error message: {error_message}"
        )
        assert "MockExternalProcess" in error_message, (
            f"Error doesn't mention external process: {error_message}"
        )

        # Verify that all API server processes were terminated as a result
        for i, proc in enumerate(manager.processes):
            assert not proc.is_alive(), f"API server process {i} was not terminated"

    finally:
        # Clean up
        manager.shutdown()
        mock_coordinator.shutdown()
        time.sleep(0.2)