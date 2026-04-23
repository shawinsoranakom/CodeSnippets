def test_watch_file(self, mock_event_watcher, mock_polling_watcher):
        """Test all possible outcomes of both `get_default_path_watcher_class` and
        `watch_file`, based on config.fileWatcherType and whether
        `watchdog_available` is true.
        """
        subtest_params = [
            (None, False, NoOpPathWatcher),
            (None, True, NoOpPathWatcher),
            ("poll", False, mock_polling_watcher),
            ("poll", True, mock_polling_watcher),
            ("watchdog", False, NoOpPathWatcher),
            ("watchdog", True, mock_event_watcher),
            ("auto", False, mock_polling_watcher),
            ("auto", True, mock_event_watcher),
        ]
        for watcher_config, watchdog_available, path_watcher_class in subtest_params:
            test_name = f"config.fileWatcherType={watcher_config}, watcher_available={watchdog_available}"
            with self.subTest(test_name):
                with patch_config_options(
                    {"server.fileWatcherType": watcher_config}
                ), patch(
                    "streamlit.watcher.path_watcher.watchdog_available",
                    watchdog_available,
                ):
                    # Test get_default_path_watcher_class() result
                    self.assertEqual(
                        path_watcher_class, get_default_path_watcher_class()
                    )

                    # Test watch_file(). If path_watcher_class is
                    # NoOpPathWatcher, nothing should happen. Otherwise,
                    # path_watcher_class should be called with the watch_file
                    # params.
                    on_file_changed = Mock()
                    watching_file = watch_file("some/file/path", on_file_changed)
                    if path_watcher_class is not NoOpPathWatcher:
                        path_watcher_class.assert_called_with(
                            "some/file/path",
                            on_file_changed,
                            glob_pattern=None,
                            allow_nonexistent=False,
                        )
                        self.assertTrue(watching_file)
                    else:
                        self.assertFalse(watching_file)