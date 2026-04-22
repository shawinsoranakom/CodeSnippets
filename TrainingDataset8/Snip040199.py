def test_file_watch_and_callback(self):
        """Test that when a file is modified, the callback is called."""
        callback = mock.Mock()

        self.util_mock.path_modification_time = lambda *args: 101.0
        self.util_mock.calc_md5_with_blocking_retries = lambda _, **kwargs: "1"

        watcher = polling_path_watcher.PollingPathWatcher(
            "/this/is/my/file.py", callback
        )

        self._run_executor_tasks()
        callback.assert_not_called()

        self.util_mock.path_modification_time = lambda *args: 102.0
        self.util_mock.calc_md5_with_blocking_retries = lambda _, **kwargs: "2"

        self._run_executor_tasks()
        callback.assert_called_once()

        watcher.close()