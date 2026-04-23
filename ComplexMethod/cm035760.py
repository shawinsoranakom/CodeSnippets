def test_maybe_setup_git_hooks_with_existing_hook(self, mock_runtime):
        # Test when there's an existing pre-commit hook
        def mock_read(action):
            if action.path == '.openhands/pre-commit.sh':
                return FileReadObservation(
                    content="#!/bin/bash\necho 'Test pre-commit hook'\nexit 0",
                    path='.openhands/pre-commit.sh',
                )
            elif action.path == '.git/hooks/pre-commit':
                # Simulate existing pre-commit hook
                return FileReadObservation(
                    content="#!/bin/bash\necho 'Existing hook'\nexit 0",
                    path='.git/hooks/pre-commit',
                )
            return ErrorObservation(content='Unexpected path')

        mock_runtime.read.side_effect = mock_read

        Runtime.maybe_setup_git_hooks(mock_runtime)

        # Verify that the runtime tried to read both scripts
        assert len(mock_runtime.read.call_args_list) >= 2

        # Verify that the runtime preserved the existing hook
        assert mock_runtime.log.call_args_list[0] == call(
            'info', 'Preserving existing pre-commit hook'
        )

        # Verify that the runtime moved the existing hook
        move_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction) and 'mv' in call[0][0].command
        ]
        assert len(move_calls) > 0

        # Verify that the runtime wrote the new pre-commit hook
        assert mock_runtime.write.called

        # Verify that the runtime logged success
        assert mock_runtime.log.call_args_list[-1] == call(
            'info', 'Git pre-commit hook installed successfully'
        )