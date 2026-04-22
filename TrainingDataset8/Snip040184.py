def test_config_watcherType(self):
        """Test server.fileWatcherType"""

        config.set_option("server.fileWatcherType", "none")
        self.assertEqual(
            local_sources_watcher.get_default_path_watcher_class().__name__,
            "NoOpPathWatcher",
        )

        config.set_option("server.fileWatcherType", "poll")
        self.assertEqual(
            local_sources_watcher.get_default_path_watcher_class().__name__,
            "PollingPathWatcher",
        )

        config.set_option("server.fileWatcherType", "watchdog")
        self.assertEqual(
            local_sources_watcher.get_default_path_watcher_class().__name__,
            "EventBasedPathWatcher" if watchdog_available else "NoOpPathWatcher",
        )

        config.set_option("server.fileWatcherType", "auto")
        self.assertIsNotNone(local_sources_watcher.get_default_path_watcher_class())

        if sys.modules["streamlit.watcher.event_based_path_watcher"] is not None:
            self.assertEqual(
                local_sources_watcher.get_default_path_watcher_class().__name__,
                "EventBasedPathWatcher",
            )
        else:
            self.assertEqual(
                local_sources_watcher.get_default_path_watcher_class().__name__,
                "PollingPathWatcher",
            )