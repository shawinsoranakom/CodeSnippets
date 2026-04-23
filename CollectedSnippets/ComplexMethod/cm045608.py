def run(self):
        self._disable_commits()
        n_times_failed = 0
        while True:
            time_before_start = time.time()
            try:
                messages = self.source.extract([self.destination.get_state()])
            except Exception:
                logging.exception(
                    "Failed to query airbyte-serverless source, retrying..."
                )
                n_times_failed += 1
                if n_times_failed == MAX_RETRIES:
                    raise
                time_elapsed = time.time() - time_before_start
                time_between_retries = 1.5**n_times_failed
                if time_elapsed < time_between_retries:
                    time.sleep(time_between_retries - time_elapsed)
                continue

            n_times_failed = 0
            self.destination.load(messages)

            if self.mode == STATIC_MODE_NAME:
                break
            if self.sync_mode == FULL_REFRESH_SYNC_MODE:
                absent_keys = set()
                for key, message in self._cache.items():
                    if key not in self._present_keys:
                        self._remove(key, message)
                        absent_keys.add(key)
                for key in absent_keys:
                    self._cache.pop(key)
                self._present_keys.clear()
            self._enable_commits()
            self._disable_commits()

            time_elapsed = time.time() - time_before_start
            if time_elapsed < self.refresh_interval:
                time.sleep(self.refresh_interval - time_elapsed)