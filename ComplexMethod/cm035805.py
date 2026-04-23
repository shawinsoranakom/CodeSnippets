def test_command_output_continuation(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        if is_windows():
            # Windows PowerShell version
            action = CmdRunAction(
                '1..5 | ForEach-Object { Write-Output $_; Start-Sleep 3 }'
            )
            action.set_hard_timeout(2.5)
            obs = runtime.run_action(action)
            assert obs.content.strip() == '1'
            assert obs.metadata.prefix == ''
            assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

            # Continue watching output
            action = CmdRunAction('')
            action.set_hard_timeout(2.5)
            obs = runtime.run_action(action)
            assert (
                '[Below is the output of the previous command.]' in obs.metadata.prefix
            )
            assert obs.content.strip() == '2'
            assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

            # Continue until completion
            for expected in ['3', '4', '5']:
                action = CmdRunAction('')
                action.set_hard_timeout(2.5)
                obs = runtime.run_action(action)
                assert (
                    '[Below is the output of the previous command.]'
                    in obs.metadata.prefix
                )
                assert obs.content.strip() == expected
                assert (
                    '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
                )

            # Final empty command to complete
            action = CmdRunAction('')
            obs = runtime.run_action(action)
            assert '[The command completed with exit code 0.]' in obs.metadata.suffix
        else:
            # Original Linux version
            # Start a command that produces output slowly
            action = CmdRunAction('for i in {1..5}; do echo $i; sleep 3; done')
            action.set_hard_timeout(2.5)
            obs = runtime.run_action(action)
            assert obs.content.strip() == '1'
            assert obs.metadata.prefix == ''
            assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

            # Continue watching output
            action = CmdRunAction('')
            action.set_hard_timeout(2.5)
            obs = runtime.run_action(action)
            assert (
                '[Below is the output of the previous command.]' in obs.metadata.prefix
            )
            assert obs.content.strip() == '2'
            assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

            # Continue until completion
            for expected in ['3', '4', '5']:
                action = CmdRunAction('')
                action.set_hard_timeout(2.5)
                obs = runtime.run_action(action)
                assert (
                    '[Below is the output of the previous command.]'
                    in obs.metadata.prefix
                )
                assert obs.content.strip() == expected
                assert (
                    '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
                )

            # Final empty command to complete
            action = CmdRunAction('')
            obs = runtime.run_action(action)
            assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    finally:
        _close_test_runtime(runtime)