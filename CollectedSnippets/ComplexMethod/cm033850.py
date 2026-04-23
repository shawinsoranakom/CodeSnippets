def _cleanup_processes(self):
        if hasattr(self, '_workers'):
            for attempts_remaining in range(C.WORKER_SHUTDOWN_POLL_COUNT - 1, -1, -1):
                if not any(worker_prc and worker_prc.is_alive() for worker_prc in self._workers):
                    break

                if attempts_remaining:
                    time.sleep(C.WORKER_SHUTDOWN_POLL_DELAY)
                else:
                    display.warning('One or more worker processes are still running and will be terminated.')

            for worker_prc in self._workers:
                if worker_prc and worker_prc.is_alive():
                    try:
                        worker_prc.terminate()
                    except AttributeError:
                        pass