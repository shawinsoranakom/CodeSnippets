def _execute_shell_command(
        self, command: str, timeout: float
    ) -> CmdOutputObservation:
        """Execute a shell command and stream its output to a callback function.

        Args:
            command: The shell command to execute
            timeout: Timeout in seconds for the command
        Returns:
            CmdOutputObservation containing the complete output and exit code
        """
        output_lines = []
        timed_out = False
        start_time = time.monotonic()

        # Use shell=True to run complex bash commands
        process = subprocess.Popen(
            ['bash', '-c', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Explicitly line-buffered for text mode
            universal_newlines=True,
            start_new_session=True,
        )
        logger.debug(
            f'[_execute_shell_command] PID of bash -c: {process.pid} for command: "{command}"'
        )

        exit_code = None

        try:
            if process.stdout:
                while process.poll() is None:
                    if (
                        timeout is not None
                        and (time.monotonic() - start_time) > timeout
                    ):
                        logger.debug(
                            f'Command "{command}" timed out after {timeout:.1f} seconds. Terminating.'
                        )
                        # Attempt to terminate the process group (SIGTERM)
                        self._safe_terminate_process(
                            process, signal_to_send=signal.SIGTERM
                        )
                        timed_out = True
                        break

                    ready_to_read, _, _ = select.select([process.stdout], [], [], 0.1)

                    if ready_to_read:
                        line = process.stdout.readline()
                        if line:
                            output_lines.append(line)
                            if self._shell_stream_callback:
                                self._shell_stream_callback(line)

            # Attempt to read any remaining data from stdout
            if process.stdout and not process.stdout.closed:
                try:
                    while line:
                        line = process.stdout.readline()
                        if line:
                            output_lines.append(line)
                            if self._shell_stream_callback:
                                self._shell_stream_callback(line)
                except Exception as e:
                    logger.warning(
                        f'Error reading directly from stdout after loop for "{command}": {e}'
                    )

            exit_code = process.returncode

            # If timeout occurred, ensure exit_code reflects this for the observation.
            if timed_out:
                exit_code = -1

        except Exception as e:
            logger.error(
                f'Outer exception in _execute_shell_command for "{command}": {e}'
            )
            if process and process.poll() is None:
                self._safe_terminate_process(process, signal_to_send=signal.SIGKILL)
            return CmdOutputObservation(
                command=command,
                content=''.join(output_lines) + f'\nError during execution: {e}',
                exit_code=-1,
            )

        complete_output = ''.join(output_lines)
        logger.debug(
            f'[_execute_shell_command] Complete output for "{command}" (len: {len(complete_output)}): {complete_output!r}'
        )
        obs_metadata = {'working_dir': self._workspace_path}
        if timed_out:
            obs_metadata['suffix'] = (
                f'[The command timed out after {timeout:.1f} seconds.]'
            )
            # exit_code = -1 # This is already set if timed_out is True

        return CmdOutputObservation(
            command=command,
            content=complete_output,
            exit_code=exit_code,
            metadata=obs_metadata,
        )