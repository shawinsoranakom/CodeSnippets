def test_overwrite_existing_file(tmp_path_factory, runtime_cls):
    temp_dir = tmp_path_factory.mktemp('mount')
    host_temp_dir = tmp_path_factory.mktemp('host')

    runtime, config = _load_runtime(temp_dir, runtime_cls)
    try:
        sandbox_dir = config.workspace_mount_path_in_sandbox
        sandbox_file = os.path.join(sandbox_dir, 'test_file.txt')

        if is_windows():
            # Check initial state
            obs = _run_cmd_action(runtime, f'Get-ChildItem -Path {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' not in obs.content

            # Create an empty file
            obs = _run_cmd_action(
                runtime, f'New-Item -ItemType File -Path {sandbox_file} -Force'
            )
            assert obs.exit_code == 0

            # Verify file exists and is empty
            obs = _run_cmd_action(runtime, f'Get-ChildItem -Path {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' in obs.content

            obs = _run_cmd_action(runtime, f'Get-Content {sandbox_file}')
            assert obs.exit_code == 0
            assert obs.content.strip() == ''  # Empty file
            assert 'Hello, World!' not in obs.content

            # Create host file and copy to overwrite
            _create_test_file(str(host_temp_dir))
            runtime.copy_to(str(host_temp_dir / 'test_file.txt'), sandbox_dir)

            # Verify file content is overwritten
            obs = _run_cmd_action(runtime, f'Get-Content {sandbox_file}')
            assert obs.exit_code == 0
            assert 'Hello, World!' in obs.content
        else:
            # Original Linux version
            obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' not in obs.content  # Check initial state

            obs = _run_cmd_action(runtime, f'touch {sandbox_file}')
            assert obs.exit_code == 0

            obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
            assert obs.exit_code == 0
            assert 'test_file.txt' in obs.content

            obs = _run_cmd_action(runtime, f'cat {sandbox_file}')
            assert obs.exit_code == 0
            assert obs.content.strip() == ''  # Empty file
            assert 'Hello, World!' not in obs.content

            _create_test_file(str(host_temp_dir))
            runtime.copy_to(str(host_temp_dir / 'test_file.txt'), sandbox_dir)

            obs = _run_cmd_action(runtime, f'cat {sandbox_file}')
            assert obs.exit_code == 0
            assert 'Hello, World!' in obs.content
    finally:
        _close_test_runtime(runtime)