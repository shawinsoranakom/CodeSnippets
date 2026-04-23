def test_watch_dir_kwarg_plumbing(self, mock_event_watcher):
        # NOTE: We only test kwarg plumbing for watch_dir since watcher_class
        # selection is tested extensively in test_watch_file, and the two
        # functions are otherwise identical.
        on_file_changed = Mock()

        watching_dir = watch_dir(
            "some/dir/path",
            on_file_changed,
            watcher_type="watchdog",
            glob_pattern="*.py",
            allow_nonexistent=True,
        )

        self.assertTrue(watching_dir)
        mock_event_watcher.assert_called_with(
            "some/dir/path",
            on_file_changed,
            glob_pattern="*.py",
            allow_nonexistent=True,
        )