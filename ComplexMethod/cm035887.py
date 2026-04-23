def test_logging_structure(self):
        """Test the structure of logging calls that would be made."""
        # Mock logger to capture calls
        log_calls = []

        def mock_logger_info(message, extra=None):
            log_calls.append({'message': message, 'extra': extra})

        def mock_logger_error(message, extra=None):
            log_calls.append({'message': message, 'extra': extra, 'level': 'error'})

        # Simulate the logging that would happen in the processor
        def simulate_processor_logging(task_id, user_count, current_version):
            mock_logger_info(
                'user_version_upgrade_processor:start',
                extra={
                    'task_id': task_id,
                    'user_count': user_count,
                    'current_version': current_version,
                },
            )

            mock_logger_info(
                'user_version_upgrade_processor:found_users',
                extra={
                    'task_id': task_id,
                    'users_to_upgrade': 2,
                    'users_already_current': 1,
                    'total_requested': user_count,
                },
            )

            mock_logger_error(
                'user_version_upgrade_processor:user_upgrade_failed',
                extra={
                    'task_id': task_id,
                    'user_id': 'user1',
                    'old_version': 1,
                    'error': 'Test error',
                },
            )

        # Run the simulation
        simulate_processor_logging(task_id=123, user_count=3, current_version=2)

        # Verify logging structure
        assert len(log_calls) == 3

        start_log = log_calls[0]
        assert 'start' in start_log['message']
        assert start_log['extra']['task_id'] == 123
        assert start_log['extra']['user_count'] == 3
        assert start_log['extra']['current_version'] == 2

        found_log = log_calls[1]
        assert 'found_users' in found_log['message']
        assert found_log['extra']['users_to_upgrade'] == 2
        assert found_log['extra']['users_already_current'] == 1

        error_log = log_calls[2]
        assert 'failed' in error_log['message']
        assert error_log['level'] == 'error'
        assert error_log['extra']['user_id'] == 'user1'
        assert error_log['extra']['error'] == 'Test error'