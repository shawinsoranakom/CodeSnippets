def test_bash_background_server(temp_dir, runtime_cls, run_as_openhands, dynamic_port):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    server_port = dynamic_port
    try:
        # Start the server, expect it to timeout (run in background manner)
        action = CmdRunAction(f'python3 -m http.server {server_port} &')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)

        if runtime_cls == CLIRuntime:
            # The '&' does not detach cleanly; the PTY session remains active.
            # the main cmd ends, then the server may receive SIGHUP.
            assert obs.exit_code == 0

            # Give the server a moment to be ready
            time.sleep(1)

            # `curl --fail` exits non-zero if connection fails or server returns an error.
            # Use a short connect timeout as the server is expected to be down.
            curl_action = CmdRunAction(
                f'curl --fail --connect-timeout 1 http://localhost:{server_port}'
            )
            curl_obs = runtime.run_action(curl_action)
            logger.info(curl_obs, extra={'msg_type': 'OBSERVATION'})
            assert isinstance(curl_obs, CmdOutputObservation)
            assert curl_obs.exit_code != 0

            # Confirm with pkill (CLIRuntime is assumed non-Windows here).
            # pkill returns 1 if no processes were matched.
            kill_action = CmdRunAction('pkill -f "http.server"')
            kill_obs = runtime.run_action(kill_action)
            logger.info(kill_obs, extra={'msg_type': 'OBSERVATION'})
            assert isinstance(kill_obs, CmdOutputObservation)
            # For CLIRuntime, bash -c "cmd &" exits quickly, orphaning "cmd".
            # CLIRuntime's timeout tries to kill the already-exited bash -c.
            # The orphaned http.server continues running.
            # So, pkill should find and kill the server.
            assert kill_obs.exit_code == 0
        else:
            assert obs.exit_code == 0

            # Give the server a moment to be ready
            time.sleep(1)

            # Verify the server is running by curling it
            if is_windows():
                curl_action = CmdRunAction(
                    f'Invoke-WebRequest -Uri http://localhost:{server_port} -UseBasicParsing | Select-Object -ExpandProperty Content'
                )
            else:
                curl_action = CmdRunAction(f'curl http://localhost:{server_port}')
            curl_obs = runtime.run_action(curl_action)
            logger.info(curl_obs, extra={'msg_type': 'OBSERVATION'})
            assert isinstance(curl_obs, CmdOutputObservation)
            assert curl_obs.exit_code == 0
            # Check for content typical of python http.server directory listing
            assert 'Directory listing for' in curl_obs.content

            # Kill the server
            if is_windows():
                # This assumes PowerShell context if LocalRuntime is used on Windows.
                kill_action = CmdRunAction('Get-Job | Stop-Job')
            else:
                kill_action = CmdRunAction('pkill -f "http.server"')
            kill_obs = runtime.run_action(kill_action)
            logger.info(kill_obs, extra={'msg_type': 'OBSERVATION'})
            assert isinstance(kill_obs, CmdOutputObservation)
            assert kill_obs.exit_code == 0

    finally:
        _close_test_runtime(runtime)