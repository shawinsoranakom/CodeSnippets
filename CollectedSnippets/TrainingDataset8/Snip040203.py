def test_multiple_watchers_same_file(self):
        """Test that we can have multiple watchers of the same file."""
        filename = "/this/is/my/file.py"

        mod_count = [0.0]

        def modify_mock_file():
            self.util_mock.path_modification_time = lambda *args: mod_count[0]
            self.util_mock.calc_md5_with_blocking_retries = (
                lambda _, **kwargs: "%d" % mod_count[0]
            )

            mod_count[0] += 1.0

        modify_mock_file()

        callback1 = mock.Mock()
        callback2 = mock.Mock()

        watcher1 = polling_path_watcher.PollingPathWatcher(filename, callback1)
        watcher2 = polling_path_watcher.PollingPathWatcher(filename, callback2)

        self._run_executor_tasks()

        callback1.assert_not_called()
        callback2.assert_not_called()

        # "Modify" our file
        modify_mock_file()
        self._run_executor_tasks()

        self.assertEqual(callback1.call_count, 1)
        self.assertEqual(callback2.call_count, 1)

        # Close watcher1. Only watcher2's callback should be called after this.
        watcher1.close()

        # Modify our file again
        modify_mock_file()
        self._run_executor_tasks()

        self.assertEqual(callback1.call_count, 1)
        self.assertEqual(callback2.call_count, 2)

        watcher2.close()

        # Modify our file a final time
        modify_mock_file()

        # Both watchers are now closed, so their callback counts
        # should not have increased.
        self.assertEqual(callback1.call_count, 1)
        self.assertEqual(callback2.call_count, 2)