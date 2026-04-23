def setUp(self):
        super(PollingPathWatcherTest, self).setUp()
        self.util_patch = mock.patch("streamlit.watcher.polling_path_watcher.util")
        self.util_mock = self.util_patch.start()

        # Patch PollingPathWatcher's thread pool executor. We want to do
        # all of our test polling on the test thread, so we accumulate
        # tasks here and run them manually via `_run_executor_tasks`.
        self._executor_tasks = []
        self.executor_patch = mock.patch(
            "streamlit.watcher.polling_path_watcher.PollingPathWatcher._executor",
        )
        executor_mock = self.executor_patch.start()
        executor_mock.submit = self._submit_executor_task

        # Patch PollingPathWatcher's `time.sleep` to no-op, so that the tasks
        # submitted to our mock executor don't block.
        self.sleep_patch = mock.patch(
            "streamlit.watcher.polling_path_watcher.time.sleep"
        )
        self.sleep_patch.start()