def test_bash_server(temp_dir, runtime_cls, run_as_openhands, dynamic_port):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Use python -u for unbuffered output, potentially helping capture initial output on Windows
        action = CmdRunAction(command=f'python -u -m http.server {dynamic_port}')
        action.set_hard_timeout(1)
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1
        assert 'Serving HTTP on' in obs.content

        if runtime_cls == CLIRuntime:
            assert '[The command timed out after 1.0 seconds.]' in obs.metadata.suffix
        else:
            assert get_timeout_suffix(1.0) in obs.metadata.suffix

        action = CmdRunAction(command='C-c', is_input=True)
        action.set_hard_timeout(30)
        obs_interrupt = runtime.run_action(action)
        logger.info(obs_interrupt, extra={'msg_type': 'OBSERVATION'})

        if runtime_cls == CLIRuntime:
            assert isinstance(obs_interrupt, ErrorObservation)
            assert (
                "CLIRuntime does not support interactive input from the agent (e.g., 'C-c'). The command 'C-c' was not sent to any process."
                in obs_interrupt.content
            )
            assert obs_interrupt.error_id == 'AGENT_ERROR$BAD_ACTION'
        else:
            assert isinstance(obs_interrupt, CmdOutputObservation)
            assert obs_interrupt.exit_code == 0
            if not is_windows():
                # Linux/macOS behavior
                assert 'Keyboard interrupt received, exiting.' in obs_interrupt.content
                assert (
                    config.workspace_mount_path_in_sandbox
                    in obs_interrupt.metadata.working_dir
                )

        # Verify the server is actually stopped by trying to start another one
        # on the same port (regardless of OS)
        action = CmdRunAction(command='ls')
        action.set_hard_timeout(3)
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        # Check that the interrupt message is NOT present in subsequent output
        assert 'Keyboard interrupt received, exiting.' not in obs.content
        # Check working directory remains correct after interrupt handling
        if runtime_cls == CLIRuntime:
            # For CLIRuntime, working_dir is the absolute host path
            assert obs.metadata.working_dir == config.workspace_base
        else:
            # For other runtimes (e.g., Docker), it's relative to or contains the sandbox path
            assert config.workspace_mount_path_in_sandbox in obs.metadata.working_dir

        # run it again!
        action = CmdRunAction(command=f'python -u -m http.server {dynamic_port}')
        action.set_hard_timeout(1)
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1
        assert 'Serving HTTP on' in obs.content

    finally:
        _close_test_runtime(runtime)