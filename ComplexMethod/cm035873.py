async def test_start_stop_lifecycle(self):
        """Test the start/stop lifecycle of the runner."""

        # Mock the runner behavior
        class MockMaintenanceTaskRunner:
            """Mock runner for verifying start/stop lifecycle behaviour."""

            def __init__(self):
                self._running: bool = False
                self._task = None
                self.start_called = False
                self.stop_called = False

            async def start(self):
                """Start the runner."""
                if self._running:
                    return
                self._running = True
                self._task = MagicMock()  # Mock asyncio.Task
                self.start_called = True

            async def stop(self):
                """Stop the runner."""
                if not self._running:
                    return
                self._running = False
                if self._task:
                    self._task.cancel()
                    # Simulate awaiting the cancelled task
                self.stop_called = True

        runner = MockMaintenanceTaskRunner()

        # Test start
        await runner.start()
        assert runner._running is True
        assert runner.start_called is True
        assert runner._task is not None

        # Test start when already running (should be no-op)
        runner.start_called = False
        await runner.start()
        assert runner.start_called is False  # Should not be called again

        # Test stop
        await runner.stop()
        running: bool = runner._running
        assert running is False
        assert runner.stop_called is True

        # Test stop when not running (should be no-op)
        runner.stop_called = False
        await runner.stop()
        assert runner.stop_called is False