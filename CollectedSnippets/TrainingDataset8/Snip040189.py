def test_passes_filepath_to_callback(self, fob):
        saved_filepath = None

        def callback(filepath):
            nonlocal saved_filepath

            saved_filepath = filepath

        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(callback)

        # Simulate a change to the report script
        lso.on_file_changed(SCRIPT_PATH)

        self.assertEqual(saved_filepath, SCRIPT_PATH)