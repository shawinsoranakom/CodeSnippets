def test_multiline_commands(temp_dir, runtime_cls):
    runtime, config = _load_runtime(temp_dir, runtime_cls)
    try:
        if is_windows():
            # Windows PowerShell version using backticks for line continuation
            obs = _run_cmd_action(runtime, 'Write-Output `\n "foo"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert 'foo' in obs.content

            # test multiline output
            obs = _run_cmd_action(runtime, 'Write-Output "hello`nworld"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert 'hello\nworld' in obs.content

            # test whitespace
            obs = _run_cmd_action(runtime, 'Write-Output "a`n`n`nz"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert '\n\n\n' in obs.content
        else:
            # Original Linux bash version
            # single multiline command
            obs = _run_cmd_action(runtime, 'echo \\\n -e "foo"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert 'foo' in obs.content

            # test multiline echo
            obs = _run_cmd_action(runtime, 'echo -e "hello\nworld"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert 'hello\nworld' in obs.content

            # test whitespace
            obs = _run_cmd_action(runtime, 'echo -e "a\\n\\n\\nz"')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            assert '\n\n\n' in obs.content
    finally:
        _close_test_runtime(runtime)