def test_git_operation(temp_dir, runtime_cls):
    # do not mount workspace, since workspace mount by tests will be owned by root
    # while the user_id we get via os.getuid() is different from root
    # which causes permission issues
    runtime, config = _load_runtime(
        temp_dir=temp_dir,
        use_workspace=False,
        runtime_cls=runtime_cls,
        # Need to use non-root user to expose issues
        run_as_openhands=True,
    )
    # this will happen if permission of runtime is not properly configured
    # fatal: detected dubious ownership in repository at config.workspace_mount_path_in_sandbox
    try:
        if runtime_cls != LocalRuntime and runtime_cls != CLIRuntime:
            # on local machine, permissionless sudo will probably not be available
            obs = _run_cmd_action(runtime, 'sudo chown -R openhands:root .')
            assert obs.exit_code == 0

        # check the ownership of the current directory
        obs = _run_cmd_action(runtime, 'ls -alh .')
        assert obs.exit_code == 0
        # drwx--S--- 2 openhands root   64 Aug  7 23:32 .
        # drwxr-xr-x 1 root      root 4.0K Aug  7 23:33 ..
        for line in obs.content.split('\n'):
            if runtime_cls == LocalRuntime or runtime_cls == CLIRuntime:
                continue  # skip these checks

            if ' ..' in line:
                # parent directory should be owned by root
                assert 'root' in line
                assert 'openhands' not in line
            elif ' .' in line:
                # current directory should be owned by openhands
                # and its group should be root
                assert 'openhands' in line
                assert 'root' in line

        # make sure all git operations are allowed
        obs = _run_cmd_action(runtime, 'git init')
        assert obs.exit_code == 0

        # create a file
        obs = _run_cmd_action(runtime, 'echo "hello" > test_file.txt')
        assert obs.exit_code == 0

        if runtime_cls == LocalRuntime or runtime_cls == CLIRuntime:
            # set git config author in CI only, not on local machine
            logger.info('Setting git config author')
            obs = _run_cmd_action(
                runtime,
                'git config user.name "openhands" && git config user.email "openhands@all-hands.dev"',
            )
            assert obs.exit_code == 0

            # Set up git config - list current settings (should be empty or just what was set)
            obs = _run_cmd_action(runtime, 'git config --list')
            assert obs.exit_code == 0

        # git add
        obs = _run_cmd_action(runtime, 'git add test_file.txt')
        assert obs.exit_code == 0

        # git diff
        obs = _run_cmd_action(runtime, 'git diff --no-color --cached')
        assert obs.exit_code == 0
        assert 'b/test_file.txt' in obs.content
        assert '+hello' in obs.content

        # git commit
        obs = _run_cmd_action(runtime, 'git commit -m "test commit"')
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)