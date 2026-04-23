def test_long_running_command_follow_by_execute(
    temp_dir, runtime_cls, run_as_openhands
):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        if is_windows():
            action = CmdRunAction('1..3 | ForEach-Object { Write-Output $_; sleep 3 }')
        else:
            # Test command that produces output slowly
            action = CmdRunAction('for i in {1..3}; do echo $i; sleep 3; done')

        action.set_hard_timeout(2.5)
        obs = runtime.run_action(action)
        assert '1' in obs.content  # First number should appear before timeout
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
        assert obs.metadata.prefix == ''

        # Continue watching output
        action = CmdRunAction('')
        action.set_hard_timeout(2.5)
        obs = runtime.run_action(action)
        assert '2' in obs.content
        assert obs.metadata.prefix == '[Below is the output of the previous command.]\n'
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running

        # Test command that produces no output
        action = CmdRunAction('sleep 15')
        action.set_hard_timeout(2.5)
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert '3' not in obs.content
        assert obs.metadata.prefix == '[Below is the output of the previous command.]\n'
        assert 'The previous command is still running' in obs.metadata.suffix
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running

        # Finally continue again
        action = CmdRunAction('')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert '3' in obs.content
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    finally:
        _close_test_runtime(runtime)