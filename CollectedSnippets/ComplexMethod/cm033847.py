def _signal_handler(self, signum, frame) -> None:
        """
        terminate all running process groups created as a result of calling
        setsid from within a WorkerProcess.

        Since the children become process leaders, signals will not
        automatically propagate to them.
        """
        signal.signal(signum, signal.SIG_DFL)

        for worker in self._workers:
            if worker is None or not worker.is_alive():
                continue
            if worker.pid:
                try:
                    # notify workers
                    os.kill(worker.pid, signum)
                except OSError as e:
                    if e.errno != errno.ESRCH:
                        signame = signal.strsignal(signum)
                        display.error(f'Unable to send {signame} to child[{worker.pid}]: {e}')

        if signum == signal.SIGINT:
            # Defer to CLI handling
            raise KeyboardInterrupt()

        pid = os.getpid()
        try:
            os.kill(pid, signum)
        except OSError as e:
            signame = signal.strsignal(signum)
            display.error(f'Unable to send {signame} to {pid}: {e}')