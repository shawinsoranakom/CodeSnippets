def test_cmd_run(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        if is_windows():
            # Windows PowerShell version
            obs = _run_cmd_action(
                runtime, f'Get-ChildItem -Path {config.workspace_mount_path_in_sandbox}'
            )
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'Get-ChildItem')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'New-Item -ItemType Directory -Path test')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'Get-ChildItem')
            assert obs.exit_code == 0
            assert 'test' in obs.content

            obs = _run_cmd_action(runtime, 'New-Item -ItemType File -Path test/foo.txt')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'Get-ChildItem test')
            assert obs.exit_code == 0
            assert 'foo.txt' in obs.content

            # clean up
            _run_cmd_action(runtime, 'Remove-Item -Recurse -Force test')
            assert obs.exit_code == 0
        else:
            # Unix version
            obs = _run_cmd_action(
                runtime, f'ls -l {config.workspace_mount_path_in_sandbox}'
            )
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'ls -l')
            assert obs.exit_code == 0
            assert 'total 0' in obs.content

            obs = _run_cmd_action(runtime, 'mkdir test')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'ls -l')
            assert obs.exit_code == 0
            if (
                run_as_openhands
                and runtime_cls != CLIRuntime
                and runtime_cls != LocalRuntime
            ):
                assert 'openhands' in obs.content
            elif runtime_cls == LocalRuntime or runtime_cls == CLIRuntime:
                # For CLI and Local runtimes, the user depends on the actual environment
                # In CI it might be a non-root user, in cloud environments it might be root
                # We just check that the command succeeded and the directory was created
                pass  # Skip user-specific assertions for environment independence
            else:
                assert 'root' in obs.content
            assert 'test' in obs.content

            obs = _run_cmd_action(runtime, 'touch test/foo.txt')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, 'ls -l test')
            assert obs.exit_code == 0
            assert 'foo.txt' in obs.content

            # clean up: this is needed, since CI will not be
            # run as root, and this test may leave a file
            # owned by root
            _run_cmd_action(runtime, 'rm -rf test')
            assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)