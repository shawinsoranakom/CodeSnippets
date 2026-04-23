async def test_concurrent_task_processing(self):
        """Test handling of multiple tasks in sequence."""

        class MockTask:
            """Mock task with configurable success or failure behaviour."""

            def __init__(self, task_id, should_fail=False):
                self.id = task_id
                self.processor_type = f'processor_{task_id}'
                self.status = 'PENDING'
                self.should_fail = should_fail

            def get_processor(self):
                """Return a mock processor."""
                processor = AsyncMock()
                if self.should_fail:
                    processor.side_effect = Exception(f'Task {self.id} failed')
                else:
                    processor.return_value = {'task_id': self.id, 'result': 'success'}
                return processor

        class MockMaintenanceTaskRunner:
            """Mock runner for verifying sequential processing of multiple tasks."""

            def __init__(self):
                self.processed_tasks = []
                self.successful_tasks = []
                self.failed_tasks = []

            async def _process_pending_tasks(self):
                """Process all pending tasks."""
                # Simulate finding multiple tasks
                tasks = [
                    MockTask(1, should_fail=False),
                    MockTask(2, should_fail=True),
                    MockTask(3, should_fail=False),
                ]

                for task in tasks:
                    await self._process_task(task)

            async def _process_task(self, task):
                """Process a single task."""
                self.processed_tasks.append(task.id)

                try:
                    processor = task.get_processor()
                    result = await processor(task)
                    self.successful_tasks.append((task.id, result))
                except Exception as e:
                    self.failed_tasks.append((task.id, str(e)))

        runner = MockMaintenanceTaskRunner()

        # Process all pending tasks
        await runner._process_pending_tasks()

        # Verify all tasks were processed
        assert len(runner.processed_tasks) == 3
        assert runner.processed_tasks == [1, 2, 3]

        # Verify success/failure handling
        assert len(runner.successful_tasks) == 2
        assert len(runner.failed_tasks) == 1

        # Check successful tasks
        successful_ids = [task_id for task_id, _ in runner.successful_tasks]
        assert 1 in successful_ids
        assert 3 in successful_ids

        # Check failed task
        failed_id, error = runner.failed_tasks[0]
        assert failed_id == 2
        assert 'Task 2 failed' in error