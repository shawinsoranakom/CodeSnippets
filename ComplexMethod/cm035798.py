def test_copy_single_file(temp_dir, runtime_cls):
    runtime, config = _load_runtime(temp_dir, runtime_cls)
    try:
        sandbox_dir = config.workspace_mount_path_in_sandbox
        sandbox_file = os.path.join(sandbox_dir, 'test_file.txt')
        _create_test_file(temp_dir)
        runtime.copy_to(os.path.join(temp_dir, 'test_file.txt'), sandbox_dir)

        if is_windows():
            obs = _run_cmd_action(runtime, f'Get-ChildItem -Path {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' in obs.content

            obs = _run_cmd_action(runtime, f'Get-Content {sandbox_file}')
            assert obs.exit_code == 0
            assert 'Hello, World!' in obs.content
        else:
            obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' in obs.content

            obs = _run_cmd_action(runtime, f'cat {sandbox_file}')
            assert obs.exit_code == 0
            assert 'Hello, World!' in obs.content
    finally:
        _close_test_runtime(runtime)