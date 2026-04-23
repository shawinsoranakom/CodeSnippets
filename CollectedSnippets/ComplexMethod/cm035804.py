def test_stress_long_output_with_soft_and_hard_timeout(
    temp_dir, runtime_cls, run_as_openhands
):
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        runtime_startup_env_vars={'NO_CHANGE_TIMEOUT_SECONDS': '1'},
        docker_runtime_kwargs={
            'cpu_period': 100000,  # 100ms
            'cpu_quota': 100000,  # Can use 100ms out of each 100ms period (1 CPU)
            'mem_limit': '4G',  # 4 GB of memory
        },
    )
    try:
        # Run a command that generates long output multiple times
        for i in range(10):
            start_time = time.time()

            # Check tmux memory usage (in KB)
            mem_action = CmdRunAction(
                'ps aux | awk \'{printf "%8.1f KB  %s\\n", $6, $0}\' | sort -nr | grep "/usr/bin/tmux" | grep -v grep | awk \'{print $1}\''
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            logger.info(
                f'Tmux memory usage (iteration {i}): {mem_obs.content.strip()} KB'
            )

            # Check action_execution_server mem
            mem_action = CmdRunAction(
                'ps aux | awk \'{printf "%8.1f KB  %s\\n", $6, $0}\' | sort -nr | grep "action_execution_server" | grep "/openhands/poetry" | grep -v grep | awk \'{print $1}\''
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            logger.info(
                f'Action execution server memory usage (iteration {i}): {mem_obs.content.strip()} KB'
            )

            # Test soft timeout
            action = CmdRunAction(
                'read -p "Do you want to continue? [Y/n] " answer; if [[ $answer == "Y" ]]; then echo "Proceeding with operation..."; echo "Operation completed successfully!"; else echo "Operation cancelled."; exit 1; fi'
            )
            obs = runtime.run_action(action)
            assert 'Do you want to continue?' in obs.content
            assert obs.exit_code == -1  # Command is still running, waiting for input

            # Send the confirmation
            action = CmdRunAction('Y', is_input=True)
            obs = runtime.run_action(action)
            assert 'Proceeding with operation...' in obs.content
            assert 'Operation completed successfully!' in obs.content
            assert obs.exit_code == 0
            assert '[The command completed with exit code 0.]' in obs.metadata.suffix

            # Test hard timeout w/ long output
            # Generate long output with 1000 asterisks per line
            action = CmdRunAction(
                f'export i={i}; for j in $(seq 1 100); do echo "Line $j - Iteration $i - $(printf \'%1000s\' | tr " " "*")"; sleep 1; done'
            )
            action.set_hard_timeout(2)
            obs = runtime.run_action(action)

            # Verify the output
            assert obs.exit_code == -1
            assert f'Line 1 - Iteration {i}' in obs.content
            # assert f'Line 1000 - Iteration {i}' in obs.content
            # assert '[The command completed with exit code 0.]' in obs.metadata.suffix

            # Because hard-timeout is triggered, the terminal will in a weird state
            # where it will not accept any new commands.
            obs = runtime.run_action(CmdRunAction('ls'))
            assert obs.exit_code == -1
            assert 'The previous command is still running' in obs.metadata.suffix

            # We need to send a Ctrl+C to reset the terminal.
            obs = runtime.run_action(CmdRunAction('C-c', is_input=True))
            assert obs.exit_code == 130

            # Now make sure the terminal is in a good state
            obs = runtime.run_action(CmdRunAction('ls'))
            assert obs.exit_code == 0

            duration = time.time() - start_time
            logger.info(f'Completed iteration {i} in {duration:.2f} seconds')

    finally:
        _close_test_runtime(runtime)