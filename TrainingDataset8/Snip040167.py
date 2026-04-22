def test_kwargs_plumbed_to_calc_md5(self):
        """Test that we pass the glob_pattern and allow_nonexistent kwargs to
        calc_md5_with_blocking_retries.

        `EventBasedPathWatcher`s can be created with optional kwargs allowing
        the caller to specify what types of files to watch (when watching a
        directory) and whether to allow watchers on paths with no files/dirs.
        This test ensures that these optional parameters make it to our hash
        calculation helpers across different on_changed events.
        """
        cb = mock.Mock()

        self.mock_util.path_modification_time = lambda *args: 101.0
        self.mock_util.calc_md5_with_blocking_retries = mock.Mock(return_value="1")

        ro = event_based_path_watcher.EventBasedPathWatcher(
            "/this/is/my/dir",
            cb,
            glob_pattern="*.py",
            allow_nonexistent=True,
        )

        fo = event_based_path_watcher._MultiPathWatcher.get_singleton()
        fo._observer.schedule.assert_called_once()

        folder_handler = fo._observer.schedule.call_args[0][0]

        _, kwargs = self.mock_util.calc_md5_with_blocking_retries.call_args
        assert kwargs == {"glob_pattern": "*.py", "allow_nonexistent": True}
        cb.assert_not_called()

        self.mock_util.path_modification_time = lambda *args: 102.0
        self.mock_util.calc_md5_with_blocking_retries = mock.Mock(return_value="3")

        ev = events.FileSystemEvent("/this/is/my/dir")
        ev.event_type = events.EVENT_TYPE_MODIFIED
        ev.is_directory = True
        folder_handler.on_modified(ev)

        _, kwargs = self.mock_util.calc_md5_with_blocking_retries.call_args
        assert kwargs == {"glob_pattern": "*.py", "allow_nonexistent": True}
        cb.assert_called_once()

        ro.close()