def test_just_script(self, fob):
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()
        args, _ = fob.call_args
        self.assertEqual(args[0], SCRIPT_PATH)
        method_type = type(self.setUp)
        self.assertEqual(type(args[1]), method_type)

        fob.reset_mock()
        lso.update_watched_modules()
        lso.update_watched_modules()
        lso.update_watched_modules()
        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 1)