def test_multiple_watchers_same_file(self):
        """Test that we can have multiple watchers of the same file."""

        filename = "/this/is/my/file.py"

        mod_count = [0.0]

        def modify_mock_file():
            self.mock_util.path_modification_time = lambda *args: mod_count[0]
            self.mock_util.calc_md5_with_blocking_retries = (
                lambda _, **kwargs: "%d" % mod_count[0]
            )

            ev = events.FileSystemEvent(filename)
            ev.event_type = events.EVENT_TYPE_MODIFIED
            folder_handler.on_modified(ev)

            mod_count[0] += 1.0

        cb1 = mock.Mock()
        cb2 = mock.Mock()

        watcher1 = event_based_path_watcher.EventBasedPathWatcher(filename, cb1)
        watcher2 = event_based_path_watcher.EventBasedPathWatcher(filename, cb2)

        fo = event_based_path_watcher._MultiPathWatcher.get_singleton()
        fo._observer.schedule.assert_called_once()

        folder_handler = fo._observer.schedule.call_args[0][0]

        cb1.assert_not_called()
        cb2.assert_not_called()

        # "Modify" our file
        modify_mock_file()

        assert 1 == cb1.call_count
        assert 1 == cb2.call_count

        # Close watcher1. Only watcher2's callback should be called after this.
        watcher1.close()

        # Modify our file again
        modify_mock_file()

        assert 1 == cb1.call_count
        assert 2 == cb2.call_count

        watcher2.close()

        # Modify our file a final time
        modify_mock_file()

        # Both watchers are now closed, so their callback counts
        # should not have increased.
        assert 1 == cb1.call_count
        assert 2 == cb2.call_count