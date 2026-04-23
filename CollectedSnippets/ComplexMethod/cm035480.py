def log_output() -> None:
        if not server_process or not server_process.stdout:
            logger.error('server process or stdout not available for logging.')
            return

        try:
            # Read lines while the process is running and stdout is available
            while server_process.poll() is None:
                if log_thread_exit_event.is_set():
                    logger.info('server log thread received exit signal.')
                    break
                line = server_process.stdout.readline()
                if not line:
                    break
                logger.info(f'server: {line.strip()}')

            # Capture any remaining output
            if not log_thread_exit_event.is_set():
                logger.info('server process exited, reading remaining output.')
                for line in server_process.stdout:
                    if log_thread_exit_event.is_set():
                        break
                    logger.info(f'server (remaining): {line.strip()}')

        except Exception as e:
            logger.error(f'Error reading server output: {e}')
        finally:
            logger.info('server log output thread finished.')