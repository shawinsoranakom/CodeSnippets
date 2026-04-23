def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Executes a command, potentially as a PowerShell background job for long-running tasks.
        Aligned with bash.py behavior regarding command execution and messages.

        Args:
            action: The command execution action.

        Returns:
            CmdOutputObservation or ErrorObservation.
        """
        if not self._initialized or self._closed:
            return ErrorObservation(
                content='PowerShell session is not initialized or has been closed.'
            )

        command = action.command.strip()
        timeout_seconds = action.timeout or 60  # Default to 60 seconds hard timeout
        is_input = action.is_input  # Check if it's intended as input

        # Detect if this is a background command (ending with &)
        run_in_background = False
        if command.endswith('&'):
            run_in_background = True
            command = command[:-1].strip()  # Remove the & and extra spaces
            logger.info(f"Detected background command: '{command}'")

        logger.info(
            f"Received command: '{command}', Timeout: {timeout_seconds}s, is_input: {is_input}, background: {run_in_background}"
        )

        # --- Simplified Active Job Handling (aligned with bash.py) ---
        with self._job_lock:
            if self.active_job:
                active_job_obj = self._get_job_object(self.active_job.Id)  # type: ignore[unreachable]
                job_is_finished = False
                final_output = ''  # Initialize before conditional assignment
                final_errors = []  # Initialize before conditional assignment
                current_job_state = None  # Initialize
                finished_job_id = (
                    self.active_job.Id
                )  # Store ID before potentially clearing self.active_job

                if active_job_obj:
                    current_job_state = active_job_obj.JobStateInfo.State
                    if current_job_state not in [JobState.Running, JobState.NotStarted]:
                        job_is_finished = True
                        logger.info(
                            f'Active job {finished_job_id} was finished ({current_job_state}) before receiving new command. Cleaning up.'
                        )
                        # Assign final output/errors here
                        final_output, final_errors = self._receive_job_output(
                            active_job_obj, keep=False
                        )  # Consume final output
                        remove_script = (
                            f'Remove-Job -Job (Get-Job -Id {finished_job_id})'
                        )
                        self._run_ps_command(remove_script)
                        # --- Reset persistent state ---
                        self._last_job_output = ''
                        self._last_job_error = []
                        self.active_job = None
                    # else: job still running, job_is_finished remains False
                else:
                    # Job object disappeared, consider it finished/gone
                    logger.warning(
                        f'Could not retrieve active job object {finished_job_id}. Assuming finished and clearing.'
                    )
                    job_is_finished = True
                    current_job_state = (
                        JobState.Failed
                    )  # Assume failed if object is gone
                    # Assign final output/errors here
                    final_output = ''  # No output retrievable
                    final_errors = ['[ERROR: Job object disappeared during check]']
                    # --- Reset persistent state ---
                    self._last_job_output = ''
                    self._last_job_error = []
                    self.active_job = None

                # If the job was found to be finished *during this check*, return its final state now.
                if job_is_finished:
                    # --- Calculate final new output/errors ---
                    new_output = final_output.removeprefix(
                        self._last_job_output
                    )  # final_output was from keep=False
                    last_error_set = set(
                        self._last_job_error
                    )  # Use the state *before* reset
                    new_errors = [e for e in final_errors if e not in last_error_set]

                    # Construct and return the observation for the completed job using the state captured during cleanup
                    exit_code = 0 if current_job_state == JobState.Completed else 1
                    output_builder = [new_output] if new_output else []
                    if new_errors:
                        output_builder.append('\\n[ERROR STREAM]')
                        output_builder.extend(new_errors)
                    content_for_return = '\\n'.join(output_builder).strip()

                    current_cwd = self._cwd  # Use cached CWD as job is gone
                    python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
                    metadata = CmdOutputMetadata(
                        exit_code=exit_code, working_dir=python_safe_cwd
                    )
                    # Indicate this output is from the *previous* command that just finished.
                    metadata.prefix = (
                        '[Below is the output of the previous command.]\\n'
                    )
                    metadata.suffix = (
                        f'\\n[The command completed with exit code {exit_code}.]'
                    )
                    logger.info(
                        f"Returning final output for job {finished_job_id} which finished before command '{command}' was processed."
                    )  # Use finished_job_id
                    return CmdOutputObservation(
                        content=content_for_return,
                        command=action.command,  # The command that triggered this check (e.g., '')
                        metadata=metadata,
                    )

                # If job was NOT finished, check incoming command
                # This block only runs if the job is still active (job_is_finished is False)
                if not job_is_finished:
                    if command == '':
                        logger.info(
                            'Received empty command while job running. Checking job status.'
                        )
                        # Pass the timeout from the empty command action to _check_active_job
                        return self._check_active_job(timeout_seconds)
                    elif command == 'C-c':
                        logger.info('Received C-c while job running. Stopping job.')
                        return self._stop_active_job()
                    elif is_input:
                        # PowerShell session doesn't directly support stdin injection like bash.py/tmux
                        # This requires a different approach (e.g., named pipes, or specific cmdlets).
                        # For now, return an error indicating this limitation.
                        logger.warning(
                            f"Received input command '{command}' while job active, but direct input injection is not supported in this implementation."
                        )
                        # Get *new* output since last observation to provide context
                        cumulative_output, cumulative_errors = self._receive_job_output(
                            self.active_job, keep=True
                        )
                        new_output = cumulative_output.removeprefix(
                            self._last_job_output
                        )
                        last_error_set = set(self._last_job_error)
                        new_errors = [
                            e for e in cumulative_errors if e not in last_error_set
                        ]
                        output_builder = [new_output] if new_output else []
                        if new_errors:
                            output_builder.append('\\n[ERROR STREAM]')
                            output_builder.extend(new_errors)
                        # --- UPDATE persistent state ---
                        # Even though input fails, the user saw this output now
                        self._last_job_output = cumulative_output
                        self._last_job_error = list(set(cumulative_errors))
                        current_cwd = self._cwd
                        python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
                        metadata = CmdOutputMetadata(
                            exit_code=-1, working_dir=python_safe_cwd
                        )  # Still running
                        metadata.prefix = (
                            '[Below is the output of the previous command.]\\n'
                        )
                        metadata.suffix = (
                            f"\\n[Your input command '{command}' was NOT processed. Direct input to running processes (is_input=True) "
                            'is not supported by this PowerShell session implementation. You can use C-c to stop the process.]'
                        )
                        return CmdOutputObservation(
                            content='\\n'.join(output_builder).strip(),
                            command=action.command,
                            metadata=metadata,
                        )

                    else:
                        # Any other command arrives while a job is running -> Reject it (bash.py behavior)
                        logger.warning(
                            f"Received new command '{command}' while job {self.active_job.Id} is active. New command NOT executed."
                        )
                        # Get *new* output since last observation to provide context
                        cumulative_output, cumulative_errors = self._receive_job_output(
                            self.active_job, keep=True
                        )
                        new_output = cumulative_output.removeprefix(
                            self._last_job_output
                        )
                        last_error_set = set(self._last_job_error)
                        new_errors = [
                            e for e in cumulative_errors if e not in last_error_set
                        ]
                        output_builder = [new_output] if new_output else []
                        if new_errors:
                            output_builder.append('\\n[ERROR STREAM]')
                            output_builder.extend(new_errors)
                        # --- UPDATE persistent state ---
                        # Even though command fails, the user saw this output now
                        self._last_job_output = cumulative_output
                        self._last_job_error = list(set(cumulative_errors))

                        current_cwd = self._cwd  # Use cached CWD
                        python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
                        metadata = CmdOutputMetadata(
                            exit_code=-1, working_dir=python_safe_cwd
                        )  # Exit code -1 indicates still running
                        metadata.prefix = (
                            '[Below is the output of the previous command.]\n'
                        )
                        metadata.suffix = (
                            f'\n[Your command "{command}" is NOT executed. '
                            f'The previous command is still running - You CANNOT send new commands until the previous command is completed. '
                            'By setting `is_input` to `true`, you can interact with the current process: '
                            f'{TIMEOUT_MESSAGE_TEMPLATE}]'
                        )

                        return CmdOutputObservation(
                            content='\\n'.join(output_builder).strip(),
                            command=action.command,  # Return the command that was attempted
                            metadata=metadata,
                        )
            # --- End Active Job Handling ---

        # --- If we reach here, there is no active job ---

        # Handle empty command when NO job is active
        if command == '':
            logger.warning('Received empty command string (no active job).')
            current_cwd = self._get_current_cwd()  # Update CWD just in case
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            metadata = CmdOutputMetadata(exit_code=0, working_dir=python_safe_cwd)
            # Align error message with bash.py
            error_content = 'ERROR: No previous running command to retrieve logs from.'
            logger.warning(
                f'Returning specific error message for empty command: {error_content}'
            )
            # No extra suffix needed
            # metadata.suffix = f"\n[Empty command received (no active job). CWD: {metadata.working_dir}]"
            return CmdOutputObservation(
                content=error_content, command='', metadata=metadata
            )

        # Handle C-* when NO job is active/relevant
        if command.startswith('C-') and len(command) == 3:
            logger.warning(
                f'Received control character command: {command}. Not supported when no job active.'
            )
            current_cwd = self._cwd  # Use cached CWD
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            # Align error message with bash.py (no running command to interact with)
            return ErrorObservation(
                content='ERROR: No previous running command to interact with.'
            )

        # --- Validate command structure using PowerShell Parser ---
        # (Keep existing validation logic as it's PowerShell specific and useful)
        parse_errors = None
        statements = None
        try:
            # Parse the input command string
            ast, _, parse_errors = Parser.ParseInput(command, None)
            if parse_errors and parse_errors.Length > 0:
                error_messages = '\n'.join(
                    [
                        f'  - {err.Message} at Line {err.Extent.StartLineNumber}, Column {err.Extent.StartColumnNumber}'
                        for err in parse_errors
                    ]
                )
                logger.error(f'Command failed PowerShell parsing:\n{error_messages}')
                return ErrorObservation(
                    content=(
                        f'ERROR: Command could not be parsed by PowerShell.\n'
                        f'Syntax errors detected:\n{error_messages}'
                    )
                )
            statements = ast.EndBlock.Statements
            if statements.Count > 1:
                logger.error(
                    f'Detected {statements.Count} statements in the command. Only one is allowed.'
                )
                # Align error message with bash.py
                splited_cmds = [
                    str(s.Extent.Text) for s in statements
                ]  # Try to get text
                return ErrorObservation(
                    content=(
                        f'ERROR: Cannot execute multiple commands at once.\n'
                        f'Please run each command separately OR chain them into a single command via PowerShell operators (e.g., ; or |).\n'
                        f'Detected commands:\n{"\n".join(f"({i + 1}) {cmd}" for i, cmd in enumerate(splited_cmds))}'
                    )
                )
            elif statements.Count == 0 and not command.strip().startswith('#'):
                logger.warning(
                    'Received command that resulted in zero executable statements (likely whitespace or comment).'
                )
                # Treat as empty command if it parses to nothing
                return CmdOutputObservation(
                    content='',
                    command=command,
                    metadata=CmdOutputMetadata(exit_code=0, working_dir=self._cwd),
                )

        except Exception as parse_ex:
            logger.exception(f'Exception during PowerShell command parsing: {parse_ex}')
            return ErrorObservation(
                content=f'ERROR: An exception occurred while parsing the command: {parse_ex}'
            )
        # --- End validation ---

        # === Synchronous Execution Path (for CWD commands) ===
        if statements and statements.Count == 1:
            statement = statements[0]
            try:
                from System.Management.Automation.Language import (
                    CommandAst,
                    PipelineAst,
                )

                # Check PipelineAst
                if isinstance(statement, PipelineAst):
                    pipeline_elements = statement.PipelineElements
                    if (
                        pipeline_elements
                        and pipeline_elements.Count == 1
                        and isinstance(pipeline_elements[0], CommandAst)
                    ):
                        command_ast = pipeline_elements[0]
                        command_name = command_ast.GetCommandName()
                        if command_name and command_name.lower() in [
                            'set-location',
                            'cd',
                            'push-location',
                            'pop-location',
                        ]:
                            logger.info(
                                f'execute: Identified CWD command via PipelineAst: {command_name}'
                            )
                            # Run command and prepare proper CmdOutputObservation
                            ps_results = self._run_ps_command(command)
                            # Get current working directory after CWD command
                            current_cwd = self._get_current_cwd()
                            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')

                            # Convert results to string output if any
                            output = (
                                '\n'.join([str(r) for r in ps_results])
                                if ps_results
                                else ''
                            )

                            return CmdOutputObservation(
                                content=output,
                                command=command,
                                metadata=CmdOutputMetadata(
                                    exit_code=0, working_dir=python_safe_cwd
                                ),
                            )
                # Check direct CommandAst
                elif isinstance(statement, CommandAst):
                    command_name = statement.GetCommandName()
                    if command_name and command_name.lower() in [
                        'set-location',
                        'cd',
                        'push-location',
                        'pop-location',
                    ]:
                        logger.info(
                            f'execute: Identified CWD command via direct CommandAst: {command_name}'
                        )
                        # Run command and prepare proper CmdOutputObservation
                        ps_results = self._run_ps_command(command)
                        # Get current working directory after CWD command
                        current_cwd = self._get_current_cwd()
                        python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')

                        # Convert results to string output if any
                        output = (
                            '\n'.join([str(r) for r in ps_results])
                            if ps_results
                            else ''
                        )

                        return CmdOutputObservation(
                            content=output,
                            command=command,
                            metadata=CmdOutputMetadata(
                                exit_code=0, working_dir=python_safe_cwd
                            ),
                        )
            except ImportError as imp_err:
                logger.error(
                    f'execute: Failed to import CommandAst: {imp_err}. Cannot check for CWD commands.'
                )
            except Exception as ast_err:
                logger.error(f'execute: Error checking command AST: {ast_err}')

        # === Asynchronous Execution Path (for non-CWD commands) ===
        logger.info(
            f"execute: Entering asynchronous execution path for command: '{command}'"
        )

        # --- Start the command as a new asynchronous job ---
        # Reset state for the new job
        self._last_job_output = ''
        self._last_job_error = []

        ps_start = None
        job = None
        output_builder = []
        all_errors = []
        exit_code = 1
        timed_out = False
        job_start_failed = False
        job_id = None

        try:
            ps_start = PowerShell.Create()
            ps_start.Runspace = self.runspace
            escaped_cwd = self._cwd.replace("'", "''")
            # Check $? after the command. If it's false, exit 1.
            start_job_script = f"Start-Job -ScriptBlock {{ Set-Location '{escaped_cwd}'; {command}; if (-not $?) {{ exit 1 }} }}"

            logger.info(f'Starting command as PowerShell job: {command}')
            ps_start.AddScript(start_job_script)
            start_results = ps_start.Invoke()

            if ps_start.Streams.Error:
                errors = [str(e) for e in ps_start.Streams.Error]
                logger.error(f'Errors during Start-Job execution: {errors}')
                all_errors.extend(errors)

            ps_get = PowerShell.Create()
            ps_get.Runspace = self.runspace
            get_job_script = 'Get-Job | Sort-Object -Property Id -Descending | Select-Object -First 1'
            ps_get.AddScript(get_job_script)
            get_results = ps_get.Invoke()

            if ps_get.Streams.Error:
                errors = [str(e) for e in ps_get.Streams.Error]
                logger.error(f'Errors getting latest job: {errors}')
                all_errors.extend(errors)
                job_start_failed = True

            if not job_start_failed and get_results and len(get_results) > 0:
                potential_job = get_results[0]
                try:
                    underlying_job = potential_job.BaseObject
                    job_state_test = underlying_job.JobStateInfo.State
                    job = underlying_job
                    job_id = job.Id

                    # For background commands, don't track the job in the session
                    if not run_in_background:
                        with self._job_lock:
                            self.active_job = job

                    logger.info(
                        f'Job retrieved successfully. Job ID: {job.Id}, State: {job_state_test}, Background: {run_in_background}'
                    )

                    if job_state_test == JobState.Failed:
                        logger.error(f'Job {job.Id} failed immediately after starting.')
                        output_chunk, error_chunk = self._receive_job_output(
                            job, keep=False
                        )
                        if output_chunk:
                            output_builder.append(output_chunk)
                        if error_chunk:
                            all_errors.extend(error_chunk)
                        job_start_failed = True
                        remove_script = f'Remove-Job -Job (Get-Job -Id {job.Id})'
                        self._run_ps_command(remove_script)
                        with self._job_lock:
                            self.active_job = None
                except AttributeError as e:
                    logger.exception(
                        f'Get-Job returned an object without expected properties on BaseObject: {e}'
                    )
                    all_errors.append('Get-Job did not return a valid Job object.')
                    job_start_failed = True

            elif not job_start_failed:
                logger.error('Get-Job did not return any results.')
                all_errors.append('Get-Job did not return any results.')
                job_start_failed = True

        except Exception as start_ex:
            logger.exception(f'Exception during job start/retrieval: {start_ex}')
            all_errors.append(f'[Job Start/Get Exception: {start_ex}]')
            job_start_failed = True
        finally:
            if ps_start:
                ps_start.Dispose()
            if 'ps_get' in locals() and ps_get:
                ps_get.Dispose()

        if job_start_failed:
            current_cwd = self._get_current_cwd()
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            metadata = CmdOutputMetadata(exit_code=1, working_dir=python_safe_cwd)
            # Use ErrorObservation for critical failures like job start
            return ErrorObservation(
                content='Failed to start PowerShell job.\n[ERRORS]\n'
                + '\n'.join(all_errors)
            )

        # For background commands, return immediately with success
        if run_in_background:
            current_cwd = self._get_current_cwd()
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            metadata = CmdOutputMetadata(exit_code=0, working_dir=python_safe_cwd)
            metadata.suffix = f'\n[Command started as background job {job_id}.]'
            return CmdOutputObservation(
                content=f'[Started background job {job_id}]',
                command=f'{command} &',
                metadata=metadata,
            )

        # --- Monitor the Job ---
        start_time = time.monotonic()
        monitoring_loop_finished = False
        shutdown_requested = False
        final_state = JobState.Failed

        latest_cumulative_output = (
            ''  # Tracks the absolute latest cumulative output seen in this loop
        )
        latest_cumulative_errors = []  # Tracks the absolute latest cumulative errors seen in this loop

        while not monitoring_loop_finished:
            if not should_continue():
                logger.warning('Shutdown signal received during job monitoring.')
                shutdown_requested = True
                monitoring_loop_finished = True
                exit_code = -1
                continue

            elapsed_seconds = time.monotonic() - start_time
            if elapsed_seconds > timeout_seconds:
                logger.warning(
                    f'Command job monitoring exceeded timeout ({timeout_seconds}s). Leaving job running.'
                )
                timed_out = True
                monitoring_loop_finished = True
                exit_code = -1
                continue

            current_job_obj = self._get_job_object(job_id)
            if not current_job_obj:
                logger.error(f'Job {job_id} object disappeared during monitoring.')
                all_errors.append('[Job object lost during monitoring]')
                monitoring_loop_finished = True
                exit_code = 1
                final_state = JobState.Failed
                # Reset state as job is gone
                self._last_job_output = ''
                self._last_job_error = []
                continue

            # Poll output (keep=True) -> Returns CUMULATIVE output/errors
            polled_cumulative_output, polled_cumulative_errors = (
                self._receive_job_output(current_job_obj, keep=True)
            )

            # Update the latest cumulative state seen in this loop
            latest_cumulative_output = polled_cumulative_output
            latest_cumulative_errors = polled_cumulative_errors

            # Check job state
            current_state = current_job_obj.JobStateInfo.State
            if current_state not in [JobState.Running, JobState.NotStarted]:
                logger.info(
                    f'Job {job_id} finished monitoring loop with state: {current_state}'
                )
                monitoring_loop_finished = True
                final_state = current_state
                continue

            time.sleep(0.1)

        # --- Monitoring loop finished ---

        job_finished_naturally = (
            not timed_out
            and not shutdown_requested
            and final_state in [JobState.Completed, JobState.Stopped, JobState.Failed]
        )

        determined_cwd = self._cwd
        final_output_content = ''
        final_error_content = []

        if job_finished_naturally:
            logger.info(
                f'Job {job_id} finished naturally with state: {final_state}. Clearing final output buffer.'
            )
            final_cumulative_output = ''
            final_cumulative_errors: list[str] = []
            final_job_obj = self._get_job_object(job_id)
            if final_job_obj:
                # Get final output/errors with keep=False
                final_cumulative_output, final_cumulative_errors = (
                    self._receive_job_output(final_job_obj, keep=False)
                )
                # Always calculate the output relative to the last observation returned
                final_output_content = final_cumulative_output.removeprefix(
                    self._last_job_output
                )
                # Also calculate final errors relative to last observation returned
                last_error_set = set(self._last_job_error)
                final_error_content = [
                    e for e in final_cumulative_errors if e not in last_error_set
                ]
            else:
                logger.warning(
                    f'Could not get final job object {job_id} to clear output buffer.'
                )
                # If object is gone, output is what was last seen relative to last observation
                final_output_content = latest_cumulative_output.removeprefix(
                    self._last_job_output
                )
                last_error_set = set(self._last_job_error)
                final_error_content = [
                    e for e in latest_cumulative_errors if e not in last_error_set
                ]

            exit_code = 0 if final_state == JobState.Completed else 1

            if final_state == JobState.Completed:
                logger.info(f'Job {job_id} completed successfully. Querying final CWD.')
                determined_cwd = self._get_current_cwd()
            else:
                logger.info(
                    f'Job {job_id} finished but did not complete successfully ({final_state}). Using cached CWD: {self._cwd}'
                )
                determined_cwd = self._cwd

            with self._job_lock:  # Lock to clear active_job
                remove_script = f'Remove-Job -Job (Get-Job -Id {job_id})'
                self._run_ps_command(remove_script)
                self.active_job = None
                logger.info(f'Cleaned up finished job {job_id}')

        else:
            logger.info(
                f'Job {job_id} did not finish naturally (timeout={timed_out}, shutdown={shutdown_requested}). Using cached CWD: {self._cwd}'
            )
            determined_cwd = self._cwd
            # Exit code is already -1 from loop exit reason

            # --- Calculate new output/errors relative to last observation (using latest from loop) ---
            final_output_content = latest_cumulative_output.removeprefix(
                self._last_job_output
            )
            final_error_content = [
                e for e in latest_cumulative_errors if e not in self._last_job_error
            ]

            # --- Update persistent state ---
            self._last_job_output = latest_cumulative_output
            self._last_job_error = list(
                set(latest_cumulative_errors)
            )  # Store unique errors

        python_safe_cwd = determined_cwd.replace('\\\\', '\\\\\\\\')

        # Combine unique output chunks for final observation
        # Using a set ensures uniqueness if chunks were identical across polls
        # Join accumulated output_builder parts
        final_output = final_output_content
        if final_error_content:  # Use the calculated final *new* errors
            error_stream_text = '\n'.join(final_error_content)
            if final_output:
                final_output += f'\n[ERROR STREAM]\n{error_stream_text}'
            else:
                final_output = f'[ERROR STREAM]\n{error_stream_text}'
            if exit_code == 0:  # Only check exit code if job finished naturally
                logger.info(
                    f'Detected errors in stream ({len(final_error_content)} records) but job state was Completed. Forcing exit_code to 1.'
                )
                exit_code = 1

        # Create metadata
        metadata = CmdOutputMetadata(exit_code=exit_code, working_dir=python_safe_cwd)

        # Determine Suffix
        if timed_out:
            # Align suffix with bash.py timeout message
            suffix = (
                f'\n[The command timed out after {timeout_seconds} seconds. '
                f'{TIMEOUT_MESSAGE_TEMPLATE}]'
            )
        elif shutdown_requested:
            # Align suffix with bash.py equivalent (though bash.py might not have specific shutdown message)
            suffix = f'\n[Command execution cancelled due to shutdown signal. Exit Code: {exit_code}]'
        elif job_finished_naturally:
            # Align suffix with bash.py completed message
            suffix = f'\n[The command completed with exit code {exit_code}.]'
        else:  # Should not happen, but defensive fallback
            suffix = f'\n[Command execution finished. State: {final_state}, Exit Code: {exit_code}]'

        metadata.suffix = suffix

        return CmdOutputObservation(
            content=final_output, command=command, metadata=metadata
        )