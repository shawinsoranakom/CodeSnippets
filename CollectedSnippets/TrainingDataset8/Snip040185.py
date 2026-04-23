def test_does_nothing_if_NoOpPathWatcher(self):
        lsw = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lsw.register_file_change_callback(NOOP_CALLBACK)
        lsw.update_watched_modules()
        self.assertEqual(len(lsw._watched_modules), 0)