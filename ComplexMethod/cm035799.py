def test_copy_directory_recursively(temp_dir, runtime_cls):
    runtime, config = _load_runtime(temp_dir, runtime_cls)

    sandbox_dir = config.workspace_mount_path_in_sandbox
    try:
        temp_dir_copy = os.path.join(temp_dir, 'test_dir')
        # We need a separate directory, since temp_dir is mounted to /workspace
        _create_host_test_dir_with_files(temp_dir_copy)

        runtime.copy_to(temp_dir_copy, sandbox_dir, recursive=True)

        if is_windows():
            obs = _run_cmd_action(runtime, f'Get-ChildItem -Path {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_dir' in obs.content
            assert 'file1.txt' not in obs.content
            assert 'file2.txt' not in obs.content

            obs = _run_cmd_action(
                runtime, f'Get-ChildItem -Path {sandbox_dir}/test_dir'
            )
            assert obs.exit_code == 0
            assert 'file1.txt' in obs.content
            assert 'file2.txt' in obs.content

            obs = _run_cmd_action(
                runtime, f'Get-Content {sandbox_dir}/test_dir/file1.txt'
            )
            assert obs.exit_code == 0
            assert 'File 1 content' in obs.content
        else:
            obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_dir' in obs.content
            assert 'file1.txt' not in obs.content
            assert 'file2.txt' not in obs.content

            obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}/test_dir')
            assert obs.exit_code == 0
            assert 'file1.txt' in obs.content
            assert 'file2.txt' in obs.content

            obs = _run_cmd_action(runtime, f'cat {sandbox_dir}/test_dir/file1.txt')
            assert obs.exit_code == 0
            assert 'File 1 content' in obs.content
    finally:
        _close_test_runtime(runtime)