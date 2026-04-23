def _check_active_job(
        self, timeout_seconds: int
    ) -> CmdOutputObservation | ErrorObservation:
        """Checks the active job for new output and status, waiting up to timeout_seconds."""
        with self._job_lock:
            if not self.active_job:
                return ErrorObservation(
                    content='ERROR: No previous running command to retrieve logs from.'
                )

            job_id = self.active_job.Id  # type: ignore[unreachable]
            logger.info(
                f'Checking active job ID: {job_id} for new output (timeout={timeout_seconds}s).'
            )

            start_time = time.monotonic()
            monitoring_loop_finished = False
            accumulated_new_output_builder = []
            accumulated_new_errors = []
            exit_code = -1  # Assume running
            final_state = JobState.Running
            latest_cumulative_output = self._last_job_output
            latest_cumulative_errors = list(self._last_job_error)

            while not monitoring_loop_finished:
                if not should_continue():
                    logger.warning('Shutdown signal received during job check.')
                    monitoring_loop_finished = True
                    continue

                elapsed_seconds = time.monotonic() - start_time
                if elapsed_seconds > timeout_seconds:
                    logger.warning(f'Job check timed out after {timeout_seconds}s.')
                    monitoring_loop_finished = True
                    continue

                current_job_obj = self._get_job_object(job_id)
                if not current_job_obj:
                    logger.error(f'Job {job_id} object disappeared during check.')
                    accumulated_new_errors.append('[Job object lost during check]')
                    monitoring_loop_finished = True
                    exit_code = 1
                    final_state = JobState.Failed
                    if self.active_job and self.active_job.Id == job_id:
                        self.active_job = None
                    continue

                # Poll output with keep=True (returns cumulative output/errors)
                polled_cumulative_output, polled_cumulative_errors = (
                    self._receive_job_output(current_job_obj, keep=True)
                )

                # Detect new output since last poll
                new_output_detected = ''
                if polled_cumulative_output != latest_cumulative_output:
                    if polled_cumulative_output.startswith(latest_cumulative_output):
                        new_output_detected = polled_cumulative_output[
                            len(latest_cumulative_output) :
                        ]
                    else:
                        logger.warning(
                            f'Job {job_id} check: Cumulative output changed unexpectedly'
                        )
                        new_output_detected = polled_cumulative_output.removeprefix(
                            self._last_job_output
                        )

                    if new_output_detected.strip():
                        accumulated_new_output_builder.append(
                            new_output_detected.strip()
                        )

                # Detect new errors
                latest_cumulative_errors_set = set(latest_cumulative_errors)
                new_errors_detected = [
                    e
                    for e in polled_cumulative_errors
                    if e not in latest_cumulative_errors_set
                ]
                if new_errors_detected:
                    accumulated_new_errors.extend(new_errors_detected)

                latest_cumulative_output = polled_cumulative_output
                latest_cumulative_errors = polled_cumulative_errors

                # Check job state
                current_state = current_job_obj.JobStateInfo.State
                if current_state not in [JobState.Running, JobState.NotStarted]:
                    logger.info(
                        f'Job {job_id} finished check loop with state: {current_state}'
                    )
                    monitoring_loop_finished = True
                    final_state = current_state
                    continue

                time.sleep(0.1)  # Prevent busy-waiting

            # Process results after loop finished
            is_finished = final_state not in [JobState.Running, JobState.NotStarted]
            final_content = '\n'.join(accumulated_new_output_builder).strip()
            final_errors = list(accumulated_new_errors)

            if is_finished:
                logger.info(f'Job {job_id} has finished. Collecting final output.')
                final_job_obj = self._get_job_object(job_id)
                if final_job_obj:
                    # Final receive with keep=False to consume remaining output
                    final_cumulative_output, final_cumulative_errors = (
                        self._receive_job_output(final_job_obj, keep=False)
                    )

                    # Check for new output in final chunk
                    final_new_output_chunk = ''
                    if final_cumulative_output.startswith(latest_cumulative_output):
                        final_new_output_chunk = final_cumulative_output[
                            len(latest_cumulative_output) :
                        ]
                    elif final_cumulative_output:
                        final_new_output_chunk = final_cumulative_output.removeprefix(
                            self._last_job_output
                        )

                    if final_new_output_chunk.strip():
                        final_content = '\n'.join(
                            filter(
                                None, [final_content, final_new_output_chunk.strip()]
                            )
                        )

                    # Check for new errors in final chunk
                    latest_cumulative_errors_set = set(latest_cumulative_errors)
                    new_final_errors = [
                        e
                        for e in final_cumulative_errors
                        if e not in latest_cumulative_errors_set
                    ]
                    if new_final_errors:
                        final_errors.extend(new_final_errors)

                    # Determine exit code based on state
                    exit_code = 0 if final_state == JobState.Completed else 1

                    # Clean up job
                    remove_script = f'Remove-Job -Job (Get-Job -Id {job_id})'
                    self._run_ps_command(remove_script)
                    if self.active_job and self.active_job.Id == job_id:
                        self.active_job = None
                    self._last_job_output = ''
                    self._last_job_error = []
                else:
                    logger.warning(f'Could not get final job object {job_id}')
                    exit_code = 1
                    if self.active_job and self.active_job.Id == job_id:
                        self.active_job = None
                    self._last_job_output = ''
                    self._last_job_error = []
            else:
                # Update persistent state with latest cumulative values
                self._last_job_output = latest_cumulative_output
                self._last_job_error = list(set(latest_cumulative_errors))

            # Append errors to final content
            if final_errors:
                error_stream_text = '\n'.join(final_errors)
                if final_content:
                    final_content += f'\n[ERROR STREAM]\n{error_stream_text}'
                else:
                    final_content = f'[ERROR STREAM]\n{error_stream_text}'
                # Ensure exit code is non-zero if errors occurred
                if exit_code == 0 and final_state != JobState.Completed:
                    exit_code = 1

            current_cwd = self._cwd
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            metadata = CmdOutputMetadata(
                exit_code=exit_code, working_dir=python_safe_cwd
            )
            metadata.prefix = '[Below is the output of the previous command.]\n'

            if is_finished:
                metadata.suffix = (
                    f'\n[The command completed with exit code {exit_code}.]'
                )
            else:
                metadata.suffix = (
                    f'\n[The command timed out after {timeout_seconds} seconds. '
                    f'{TIMEOUT_MESSAGE_TEMPLATE}]'
                )

            return CmdOutputObservation(
                content=final_content,
                command='',
                metadata=metadata,
            )