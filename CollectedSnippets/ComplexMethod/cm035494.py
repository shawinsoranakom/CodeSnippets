def _receive_job_output(
        self, job: System.Management.Automation.Job, keep: bool = False
    ) -> tuple[str, list[str]]:
        """Receives output and errors from a job."""
        if not job:
            return '', []

        output_parts = []
        error_parts = []

        # Get error stream directly from job object if available
        try:
            current_job_obj = self._get_job_object(job.Id)
            if current_job_obj and current_job_obj.Error:
                error_records = current_job_obj.Error.ReadAll()
                if error_records:
                    error_parts.extend([str(e) for e in error_records])
        except Exception as read_err:
            logger.error(
                f'Failed to read job error stream directly for Job {job.Id}: {read_err}'
            )
            error_parts.append(f'[Direct Error Stream Read Exception: {read_err}]')

        # Run Receive-Job for the output stream
        keep_switch = '-Keep' if keep else ''
        script = f'Receive-Job -Job (Get-Job -Id {job.Id}) {keep_switch}'

        ps_receive = None
        try:
            ps_receive = PowerShell.Create()
            ps_receive.Runspace = self.runspace
            ps_receive.AddScript(script)

            # Collect output
            results = ps_receive.Invoke()
            if results:
                output_parts = [str(r) for r in results]

            # Collect errors from the Receive-Job command
            if ps_receive.Streams.Error:
                receive_job_errors = [str(e) for e in ps_receive.Streams.Error]
                logger.warning(
                    f'Errors during Receive-Job for Job ID {job.Id}: {receive_job_errors}'
                )
                error_parts.extend(receive_job_errors)

        except Exception as e:
            logger.error(f'Exception during Receive-Job for Job ID {job.Id}: {e}')
            error_parts.append(f'[Receive-Job Exception: {e}]')
        finally:
            if ps_receive:
                ps_receive.Dispose()

        final_combined_output = '\n'.join(output_parts)
        return final_combined_output, error_parts