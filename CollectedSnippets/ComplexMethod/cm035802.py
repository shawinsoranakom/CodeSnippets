def test_basic_command(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        if is_windows():
            # Test simple command
            obs = _run_cmd_action(runtime, "Write-Output 'hello world'")
            assert 'hello world' in obs.content
            assert obs.exit_code == 0

            # Test command with error
            obs = _run_cmd_action(runtime, 'nonexistent_command')
            assert obs.exit_code != 0
            assert 'not recognized' in obs.content or 'command not found' in obs.content

            # Test command with special characters
            obs = _run_cmd_action(
                runtime, 'Write-Output "hello   world    with`nspecial  chars"'
            )
            assert 'hello   world    with\nspecial  chars' in obs.content
            assert obs.exit_code == 0

            # Test multiple commands in sequence
            obs = _run_cmd_action(
                runtime,
                'Write-Output "first" && Write-Output "second" && Write-Output "third"',
            )
            assert 'first' in obs.content
            assert 'second' in obs.content
            assert 'third' in obs.content
            assert obs.exit_code == 0
        else:
            # Original Linux version
            # Test simple command
            obs = _run_cmd_action(runtime, "echo 'hello world'")
            assert 'hello world' in obs.content
            assert obs.exit_code == 0

            # Test command with error
            obs = _run_cmd_action(runtime, 'nonexistent_command')
            assert obs.exit_code == 127
            assert 'nonexistent_command: command not found' in obs.content

            # Test command with special characters
            obs = _run_cmd_action(
                runtime, "echo 'hello   world    with\nspecial  chars'"
            )
            assert 'hello   world    with\nspecial  chars' in obs.content
            assert obs.exit_code == 0

            # Test multiple commands in sequence
            obs = _run_cmd_action(
                runtime, 'echo "first" && echo "second" && echo "third"'
            )
            assert 'first' in obs.content
            assert 'second' in obs.content
            assert 'third' in obs.content
            assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)