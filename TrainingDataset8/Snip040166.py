def test_works_with_directories(self):
        """Test that when a directory is modified, the callback is called."""
        cb = mock.Mock()

        self.mock_util.path_modification_time = lambda *args: 101.0
        self.mock_util.calc_md5_with_blocking_retries = lambda _, **kwargs: "1"

        ro = event_based_path_watcher.EventBasedPathWatcher("/this/is/my/dir", cb)

        fo = event_based_path_watcher._MultiPathWatcher.get_singleton()
        fo._observer.schedule.assert_called_once()

        folder_handler = fo._observer.schedule.call_args[0][0]

        cb.assert_not_called()

        self.mock_util.path_modification_time = lambda *args: 102.0
        self.mock_util.calc_md5_with_blocking_retries = lambda _, **kwargs: "2"

        ev = events.FileSystemEvent("/this/is/my/dir")
        ev.event_type = events.EVENT_TYPE_MODIFIED
        ev.is_directory = True
        folder_handler.on_modified(ev)

        cb.assert_called_once()

        ro.close()