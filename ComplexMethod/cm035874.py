async def test_task_processing_success(self):
        """Test successful task processing."""

        # Mock task processing logic
        class MockTask:
            """Mock task for successful processing scenarios."""

            def __init__(self, task_id, processor_type):
                self.id = task_id
                self.processor_type = processor_type
                self.status = 'PENDING'
                self.info = None
                self.updated_at = None

            def get_processor(self):
                """Return a mock processor."""
                # Mock processor
                processor = AsyncMock()
                processor.return_value = {'result': 'success', 'processed_items': 5}
                return processor

        class MockMaintenanceTaskRunner:
            """Mock runner for verifying task status transitions on success."""

            def __init__(self):
                self.status_updates = []
                self.commits = []

            async def _process_task(self, task):
                """Process a single task."""
                # Simulate updating status to WORKING
                task.status = 'WORKING'
                task.updated_at = datetime.now()
                self.status_updates.append(('WORKING', task.id))
                self.commits.append('working_commit')

                try:
                    # Get and execute processor
                    processor = task.get_processor()
                    result = await processor(task)

                    # Mark as completed
                    task.status = 'COMPLETED'
                    task.info = result
                    task.updated_at = datetime.now()
                    self.status_updates.append(('COMPLETED', task.id))
                    self.commits.append('completed_commit')

                    return result
                except Exception as e:
                    # Handle error (not expected in this test)
                    task.status = 'ERROR'
                    task.info = {'error': str(e)}
                    self.status_updates.append(('ERROR', task.id))
                    self.commits.append('error_commit')
                    raise

        runner = MockMaintenanceTaskRunner()
        task = MockTask(123, 'test_processor')

        # Process the task
        result = await runner._process_task(task)

        # Verify the processing flow
        assert len(runner.status_updates) == 2
        assert runner.status_updates[0] == ('WORKING', 123)
        assert runner.status_updates[1] == ('COMPLETED', 123)
        assert len(runner.commits) == 2
        assert task.status == 'COMPLETED'
        assert task.info == {'result': 'success', 'processed_items': 5}
        assert result == {'result': 'success', 'processed_items': 5}