def _safe_terminate_process(self, process_obj, signal_to_send=signal.SIGTERM):
        """Safely attempts to terminate/kill a process group or a single process.

        Args:
            process_obj: the subprocess.Popen object started with start_new_session=True
            signal_to_send: the signal to send to the process group or process.
        """
        pid = getattr(process_obj, 'pid', None)
        if pid is None:
            return

        group_desc = (
            'kill process group'
            if signal_to_send == signal.SIGKILL
            else 'terminate process group'
        )
        process_desc = (
            'kill process' if signal_to_send == signal.SIGKILL else 'terminate process'
        )

        try:
            # Try to terminate/kill the entire process group
            logger.debug(f'[_safe_terminate_process] Original PID to act on: {pid}')
            pgid_to_kill = os.getpgid(
                pid
            )  # This might raise ProcessLookupError if pid is already gone
            logger.debug(
                f'[_safe_terminate_process] Attempting to {group_desc} for PID {pid} (PGID: {pgid_to_kill}) with {signal_to_send}.'
            )
            os.killpg(pgid_to_kill, signal_to_send)
            logger.debug(
                f'[_safe_terminate_process] Successfully sent signal {signal_to_send} to PGID {pgid_to_kill} (original PID: {pid}).'
            )
        except ProcessLookupError as e_pgid:
            logger.warning(
                f'[_safe_terminate_process] ProcessLookupError getting PGID for PID {pid} (it might have already exited): {e_pgid}. Falling back to direct kill/terminate.'
            )
            try:
                if signal_to_send == signal.SIGKILL:
                    process_obj.kill()
                else:
                    process_obj.terminate()
                logger.debug(
                    f'[_safe_terminate_process] Fallback: Terminated {process_desc} (PID: {pid}).'
                )
            except Exception as e_fallback:
                logger.error(
                    f'[_safe_terminate_process] Fallback: Error during {process_desc} (PID: {pid}): {e_fallback}'
                )
        except (AttributeError, OSError) as e_os:
            logger.error(
                f'[_safe_terminate_process] OSError/AttributeError during {group_desc} for PID {pid}: {e_os}. Falling back.'
            )
            # Fallback: try to terminate/kill the main process directly.
            try:
                if signal_to_send == signal.SIGKILL:
                    process_obj.kill()
                else:
                    process_obj.terminate()
                logger.debug(
                    f'[_safe_terminate_process] Fallback: Terminated {process_desc} (PID: {pid}).'
                )
            except Exception as e_fallback:
                logger.error(
                    f'[_safe_terminate_process] Fallback: Error during {process_desc} (PID: {pid}): {e_fallback}'
                )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            logger.error(f'Error: {e}')