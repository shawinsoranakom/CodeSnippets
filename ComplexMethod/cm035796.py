def test_run_as_user_correct_home_dir(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        if is_windows():
            # Windows PowerShell version
            obs = _run_cmd_action(runtime, 'cd $HOME && Get-Location')
            assert obs.exit_code == 0
            # Check for Windows-style home paths
            if runtime_cls == LocalRuntime:
                assert (
                    os.getenv('USERPROFILE') in obs.content
                    or os.getenv('HOME') in obs.content
                )
            # For non-local runtime, we are less concerned with precise paths
        else:
            # Original Linux version
            obs = _run_cmd_action(runtime, 'cd ~ && pwd')
            assert obs.exit_code == 0
            if runtime_cls == LocalRuntime:
                assert os.getenv('HOME') in obs.content
            elif run_as_openhands:
                assert '/home/openhands' in obs.content
            else:
                assert '/root' in obs.content
    finally:
        _close_test_runtime(runtime)