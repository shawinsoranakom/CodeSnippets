def test_multiple_multiline_commands(temp_dir, runtime_cls, run_as_openhands):
    if is_windows():
        cmds = [
            'Get-ChildItem',
            'Write-Output "hello`nworld"',
            """Write-Output "hello it's me\"""",
            """Write-Output `
    ('hello ' + `
    'world')""",
            """Write-Output 'hello\nworld\nare\nyou\nthere?'""",
            """Write-Output 'hello\nworld\nare\nyou\n\nthere?'""",
            """Write-Output 'hello\nworld "'""",  # Escape the trailing double quote
        ]
    else:
        cmds = [
            'ls -l',
            'echo -e "hello\nworld"',
            """echo -e "hello it's me\"""",
            """echo \\
    -e 'hello' \\
    world""",
            """echo -e 'hello\\nworld\\nare\\nyou\\nthere?'""",
            """echo -e 'hello\nworld\nare\nyou\n\nthere?'""",
            """echo -e 'hello\nworld "'""",
        ]
    joined_cmds = '\n'.join(cmds)

    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # First test that running multiple commands at once fails
        obs = _run_cmd_action(runtime, joined_cmds)
        assert isinstance(obs, ErrorObservation)
        assert 'Cannot execute multiple commands at once' in obs.content

        # Now run each command individually and verify they work
        results = []
        for cmd in cmds:
            obs = _run_cmd_action(runtime, cmd)
            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == 0
            results.append(obs.content)

        # Verify all expected outputs are present
        if is_windows():
            # Get-ChildItem should execute successfully (no specific content check needed)
            pass  # results[0] contains directory listing output
        else:
            assert 'total 0' in results[0]  # ls -l
        assert 'hello\nworld' in results[1]  # echo -e "hello\nworld"
        assert "hello it's me" in results[2]  # echo -e "hello it\'s me"
        assert 'hello world' in results[3]  # echo -e 'hello' world
        assert (
            'hello\nworld\nare\nyou\nthere?' in results[4]
        )  # echo -e 'hello\nworld\nare\nyou\nthere?'
        assert (
            'hello\nworld\nare\nyou\n\nthere?' in results[5]
        )  # echo -e with literal newlines
        assert 'hello\nworld "' in results[6]  # echo -e with quote
    finally:
        _close_test_runtime(runtime)