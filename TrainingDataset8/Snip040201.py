def test_callback_not_called_if_same_md5(self):
        """Test that we ignore files with same md5."""
        callback = mock.Mock()

        self.util_mock.path_modification_time = lambda *args: 101.0
        self.util_mock.calc_md5_with_blocking_retries = lambda _, **kwargs: "1"

        watcher = polling_path_watcher.PollingPathWatcher(
            "/this/is/my/file.py", callback
        )

        self._run_executor_tasks()
        callback.assert_not_called()

        self.util_mock.path_modification_time = lambda *args: 102.0
        # Same MD5

        # This is the test:
        self._run_executor_tasks()
        callback.assert_not_called()

        watcher.close()