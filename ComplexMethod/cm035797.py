def test_stateful_cmd(temp_dir, runtime_cls):
    runtime, config = _load_runtime(temp_dir, runtime_cls)
    try:
        if is_windows():
            # Windows PowerShell version
            obs = _run_cmd_action(
                runtime, 'New-Item -ItemType Directory -Path test -Force'
            )
            assert obs.exit_code == 0, 'The exit code should be 0.'

            obs = _run_cmd_action(runtime, 'Set-Location test')
            assert obs.exit_code == 0, 'The exit code should be 0.'

            obs = _run_cmd_action(runtime, 'Get-Location')
            assert obs.exit_code == 0, 'The exit code should be 0.'
            # Account for both forward and backward slashes in path
            norm_path = config.workspace_mount_path_in_sandbox.replace(
                '\\', '/'
            ).replace('//', '/')
            test_path = f'{norm_path}/test'.replace('//', '/')
            assert test_path in obs.content.replace('\\', '/')
        else:
            # Original Linux version
            obs = _run_cmd_action(runtime, 'mkdir -p test')
            assert obs.exit_code == 0, 'The exit code should be 0.'

            if runtime_cls == CLIRuntime:
                # For CLIRuntime, test CWD change and command execution within a single action
                # as CWD is enforced in the workspace.
                obs = _run_cmd_action(runtime, 'cd test && pwd')
            else:
                # For other runtimes, test stateful CWD change across actions
                obs = _run_cmd_action(runtime, 'cd test')
                assert obs.exit_code == 0, 'The exit code should be 0 for cd test.'
                obs = _run_cmd_action(runtime, 'pwd')

            assert obs.exit_code == 0, (
                'The exit code for the pwd command (or combined command) should be 0.'
            )
            assert (
                f'{config.workspace_mount_path_in_sandbox}/test' in obs.content.strip()
            )
    finally:
        _close_test_runtime(runtime)