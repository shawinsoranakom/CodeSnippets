def test_python_interactive_input_without_set_input(
    temp_dir, runtime_cls, run_as_openhands
):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test Python program that asks for input
        python_script = """name = input('Enter your name: '); age = input('Enter your age: '); print(f'Hello {name}, you are {age} years old')"""

        # Start Python with the interactive script
        obs = runtime.run_action(CmdRunAction(f'python -c "{python_script}"'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Enter your name:' in obs.content
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running

        # Send first input (name)
        obs = runtime.run_action(CmdRunAction('Alice', is_input=False))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Enter your age:' not in obs.content
        assert (
            'Your command "Alice" is NOT executed. The previous command is still running'
            in obs.metadata.suffix
        )
        assert obs.metadata.exit_code == -1

        # Try again now with input
        obs = runtime.run_action(CmdRunAction('Alice', is_input=True))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Enter your age:' in obs.content
        assert obs.metadata.exit_code == -1

        obs = runtime.run_action(CmdRunAction('25', is_input=True))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Hello Alice, you are 25 years old' in obs.content
        assert obs.metadata.exit_code == 0
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    finally:
        _close_test_runtime(runtime)