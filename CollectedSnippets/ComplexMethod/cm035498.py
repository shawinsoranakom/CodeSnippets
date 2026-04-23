def close(self) -> None:
        """Closes the PowerShell runspace and releases resources, stopping any active job."""
        if self._closed:
            return

        logger.info('Closing PowerShell session runspace.')

        # Stop and remove any active job before closing runspace
        with self._job_lock:
            if self.active_job:
                logger.warning(  # type: ignore[unreachable]
                    f'Session closing with active job {self.active_job.Id}. Attempting to stop and remove.'
                )
                job_id = self.active_job.Id
                try:
                    # Ensure job object exists before trying to stop/remove
                    active_job_obj = self._get_job_object(job_id)
                    if active_job_obj:
                        stop_script = f'Stop-Job -Job (Get-Job -Id {job_id})'
                        self._run_ps_command(
                            stop_script
                        )  # Use helper before runspace closes
                        time.sleep(0.1)
                        remove_script = f'Remove-Job -Job (Get-Job -Id {job_id})'
                        self._run_ps_command(remove_script)
                        logger.info(
                            f'Stopped and removed active job {job_id} during close.'
                        )
                    else:
                        logger.warning(
                            f'Could not find job object {job_id} to stop/remove during close.'
                        )
                except Exception as e:
                    logger.error(
                        f'Error stopping/removing job {job_id} during close: {e}'
                    )
                # --- Reset state even if stop/remove failed ---
                self._last_job_output = ''
                self._last_job_error = []
                self.active_job = None

        if hasattr(self, 'runspace') and self.runspace:
            try:
                # Check state using System.Management.Automation.Runspaces namespace
                # Get the state info object first to avoid potential pythonnet issues with nested access
                runspace_state_info = self.runspace.RunspaceStateInfo
                if runspace_state_info.State == RunspaceState.Opened:
                    self.runspace.Close()
                self.runspace.Dispose()
                logger.info('PowerShell runspace closed and disposed.')
            except Exception as e:
                logger.exception(f'Error closing/disposing PowerShell runspace: {e}')

        self.runspace = None
        self._initialized = False
        self._closed = True