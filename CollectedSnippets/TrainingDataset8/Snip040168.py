def test_callback_not_called_if_same_mtime(self):
        """Test that we ignore files with same mtime."""
        cb = mock.Mock()

        self.mock_util.path_modification_time = lambda *args: 101.0
        self.mock_util.calc_md5_with_blocking_retries = lambda _, **kwargs: "1"

        ro = event_based_path_watcher.EventBasedPathWatcher("/this/is/my/file.py", cb)

        fo = event_based_path_watcher._MultiPathWatcher.get_singleton()
        fo._observer.schedule.assert_called_once()

        folder_handler = fo._observer.schedule.call_args[0][0]

        cb.assert_not_called()

        # Same mtime!
        self.mock_util.calc_md5_with_blocking_retries = lambda _, **kwargs: "2"

        ev = events.FileSystemEvent("/this/is/my/file.py")
        ev.event_type = events.EVENT_TYPE_MODIFIED
        folder_handler.on_modified(ev)

        # This is the test:
        cb.assert_not_called()

        ro.close()