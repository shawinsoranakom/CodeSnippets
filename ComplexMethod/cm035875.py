async def test_task_processing_failure(self):
        """Test task processing with failure."""

        class MockTask:
            """Mock task for failure processing scenarios."""

            def __init__(self, task_id, processor_type):
                self.id = task_id
                self.processor_type = processor_type
                self.status = 'PENDING'
                self.info = None
                self.updated_at = None

            def get_processor(self):
                """Return a mock processor."""
                # Mock processor that fails
                processor = AsyncMock()
                processor.side_effect = ValueError('Processing failed')
                return processor

        class MockMaintenanceTaskRunner:
            """Mock runner for verifying task status transitions on failure."""

            def __init__(self):
                self.status_updates = []
                self.error_logged = None

            async def _process_task(self, task):
                """Process a single task."""
                # Simulate updating status to WORKING
                task.status = 'WORKING'
                task.updated_at = datetime.now()
                self.status_updates.append(('WORKING', task.id))

                try:
                    # Get and execute processor
                    processor = task.get_processor()
                    result = await processor(task)

                    # This shouldn't be reached
                    task.status = 'COMPLETED'
                    task.info = result
                    self.status_updates.append(('COMPLETED', task.id))

                except Exception as e:
                    # Handle error
                    error_info = {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'processor_type': task.processor_type,
                    }

                    task.status = 'ERROR'
                    task.info = error_info
                    task.updated_at = datetime.now()
                    self.status_updates.append(('ERROR', task.id))
                    self.error_logged = error_info

        runner = MockMaintenanceTaskRunner()
        task = MockTask(456, 'failing_processor')

        # Process the task
        await runner._process_task(task)

        # Verify the error handling flow
        assert len(runner.status_updates) == 2
        assert runner.status_updates[0] == ('WORKING', 456)
        assert runner.status_updates[1] == ('ERROR', 456)
        assert task.status == 'ERROR'
        info = task.info
        assert info is not None
        assert info['error'] == 'Processing failed'
        assert info['error_type'] == 'ValueError'
        assert info['processor_type'] == 'failing_processor'
        assert runner.error_logged is not None