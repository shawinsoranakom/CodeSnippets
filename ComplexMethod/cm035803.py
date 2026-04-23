def test_interactive_command(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        runtime_startup_env_vars={'NO_CHANGE_TIMEOUT_SECONDS': '1'},
    )
    try:
        # Test interactive command
        action = CmdRunAction('read -p "Enter name: " name && echo "Hello $name"')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        # This should trigger SOFT timeout, so no need to set hard timeout
        assert 'Enter name:' in obs.content
        assert '[The command has no new output after 1 seconds.' in obs.metadata.suffix

        action = CmdRunAction('John', is_input=True)
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Hello John' in obs.content
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix

        # Test multiline command input with here document
        action = CmdRunAction("""cat << EOF
line 1
line 2
EOF""")
        obs = runtime.run_action(action)
        assert 'line 1\nline 2' in obs.content
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)