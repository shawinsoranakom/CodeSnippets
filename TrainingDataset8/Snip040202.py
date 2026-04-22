def test_kwargs_plumbed_to_calc_md5(self):
        """Test that we pass the glob_pattern and allow_nonexistent kwargs to
        calc_md5_with_blocking_retries.

        `PollingPathWatcher`s can be created with optional kwargs allowing
        the caller to specify what types of files to watch (when watching a
        directory) and whether to allow watchers on paths with no files/dirs.
        This test ensures that these optional parameters make it to our hash
        calculation helpers across different on_changed events.
        """
        callback = mock.Mock()

        self.util_mock.path_modification_time = lambda *args: 101.0
        self.util_mock.calc_md5_with_blocking_retries = mock.Mock(return_value="1")

        watcher = polling_path_watcher.PollingPathWatcher(
            "/this/is/my/dir",
            callback,
            glob_pattern="*.py",
            allow_nonexistent=True,
        )

        self._run_executor_tasks()
        callback.assert_not_called()
        _, kwargs = self.util_mock.calc_md5_with_blocking_retries.call_args
        assert kwargs == {"glob_pattern": "*.py", "allow_nonexistent": True}

        self.util_mock.path_modification_time = lambda *args: 102.0
        self.util_mock.calc_md5_with_blocking_retries = mock.Mock(return_value="2")

        self._run_executor_tasks()
        callback.assert_called_once()
        _, kwargs = self.util_mock.calc_md5_with_blocking_retries.call_args
        assert kwargs == {"glob_pattern": "*.py", "allow_nonexistent": True}

        watcher.close()