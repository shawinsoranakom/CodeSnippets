def test_callback_not_called_if_same_mtime(self):
        """Test that we ignore files with same mtime."""
        callback = mock.Mock()

        self.util_mock.path_modification_time = lambda *args: 101.0
        self.util_mock.calc_md5_with_blocking_retries = lambda _, **kwargs: "1"

        watcher = polling_path_watcher.PollingPathWatcher(
            "/this/is/my/file.py", callback
        )

        self._run_executor_tasks()
        callback.assert_not_called()

        # Same mtime!
        self.util_mock.calc_md5_with_blocking_retries = lambda _, **kwargs: "2"

        # This is the test:
        self._run_executor_tasks()
        callback.assert_not_called()

        watcher.close()