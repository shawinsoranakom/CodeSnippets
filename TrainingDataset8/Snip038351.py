def _schedule(self) -> None:
        def task():
            time.sleep(_POLLING_PERIOD_SECS)
            self._check_if_path_changed()

        PollingPathWatcher._executor.submit(task)